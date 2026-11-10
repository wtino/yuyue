//! 反馈, sealed before it leaves the device.
//!
//! The apps build a short report (what the person wrote, plus the app version and
//! the OS — never a book, a note, or a device id) and this seals it to one public
//! key. The bytes are a libsodium sealed box (`crypto_box_seal`): anyone can write
//! one, only the private key can open it. That key stays in the private relay, not
//! in the app.

use std::time::{SystemTime, UNIX_EPOCH};

use base64::Engine as _;
use base64::engine::general_purpose::STANDARD;
use crypto_box::aead::OsRng;
use crypto_box::PublicKey;
#[cfg(test)]
use crypto_box::SecretKey;
use serde::Serialize;

use crate::error::{CoreError, Result};

/// How long the written text may be. ntfy.sh keeps a message under 4096 bytes,
/// and a sealed box grows on the way out, so the cap is on the characters.
pub const TEXT_MAX: usize = 800;
pub const CONTACT_MAX: usize = 80;
/// UTF-8 of the JSON, before the seal. Keeps `v1.` + base64 under 4096 bytes.
const PLAIN_MAX: usize = 3000;

/// What the person chose to send. The apps fill `app_version`, `platform` and
/// `os_version` from the system; they are not identifiers.
#[derive(Clone, Debug, uniffi::Record)]
pub struct FeedbackDraft {
    /// `bug`, `idea` or `other`.
    pub category: String,
    pub text: String,
    pub contact: String,
    pub app_version: String,
    pub platform: String,
    pub os_version: String,
}

#[derive(Serialize)]
struct Payload<'a> {
    v: u32,
    category: &'a str,
    text: &'a str,
    contact: &'a str,
    app: &'a str,
    platform: &'a str,
    os: &'a str,
    #[serde(rename = "sentAt")]
    sent_at: u64,
}

/// Seal `draft` for `public_key_b64` (standard base64 of the 32-byte X25519 key).
///
/// Returns `v1.` plus the standard base64 of the sealed box, ready to POST as the
/// body of one ntfy message.
#[uniffi::export]
pub fn seal_feedback(public_key_b64: String, draft: FeedbackDraft) -> Result<String> {
    let text = draft.text.trim();
    let contact = draft.contact.trim();
    if text.is_empty() {
        return Err(CoreError::Invalid { detail: "empty".into() });
    }
    if text.chars().count() > TEXT_MAX || contact.chars().count() > CONTACT_MAX {
        return Err(CoreError::Invalid { detail: "too long".into() });
    }
    let category = match draft.category.as_str() {
        "bug" | "idea" | "other" => draft.category.as_str(),
        _ => return Err(CoreError::Invalid { detail: "category".into() }),
    };
    let key = decode_key(&public_key_b64)?;
    let public_key = PublicKey::from_slice(&key).map_err(|_| CoreError::Invalid { detail: "public key".into() })?;
    let payload = Payload {
        v: 1,
        category,
        text,
        contact,
        app: &clip(&draft.app_version, 80),
        platform: &clip(&draft.platform, 40),
        os: &clip(&draft.os_version, 80),
        sent_at: now_ms(),
    };
    let plain = serde_json::to_vec(&payload)?;
    if plain.len() > PLAIN_MAX {
        return Err(CoreError::Invalid { detail: "too long".into() });
    }
    let sealed = public_key.seal(&mut OsRng, &plain).map_err(|_| CoreError::Invalid { detail: "seal".into() })?;
    let body = format!("v1.{}", STANDARD.encode(sealed));
    if body.len() > 4096 {
        return Err(CoreError::Invalid { detail: "too long".into() });
    }
    Ok(body)
}

fn decode_key(text: &str) -> Result<[u8; 32]> {
    let cleaned: String = text.chars().filter(|c| !c.is_whitespace()).collect();
    let bytes = STANDARD.decode(cleaned.as_bytes()).map_err(|_| CoreError::Invalid { detail: "public key".into() })?;
    bytes.try_into().map_err(|_| CoreError::Invalid { detail: "public key".into() })
}

fn clip(text: &str, max: usize) -> String {
    text.trim().chars().take(max).collect()
}

fn now_ms() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_millis() as u64).unwrap_or(0)
}

/// Open a `v1.` body with the 32-byte secret. Tests and the relay use this shape;
/// the apps never call it.
#[cfg(test)]
fn open_feedback(secret: &[u8], body: &str) -> Result<Vec<u8>> {
    let raw = body.strip_prefix("v1.").ok_or_else(|| CoreError::Invalid { detail: "body".into() })?;
    let sealed = STANDARD.decode(raw).map_err(|_| CoreError::Invalid { detail: "body".into() })?;
    let secret = SecretKey::from_slice(secret).map_err(|_| CoreError::Invalid { detail: "secret".into() })?;
    secret.unseal(&sealed).map_err(|_| CoreError::Invalid { detail: "seal".into() })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn roundtrip(draft: FeedbackDraft) -> serde_json::Value {
        let secret = SecretKey::generate(&mut OsRng);
        let public_key = STANDARD.encode(secret.public_key().as_bytes());
        let body = seal_feedback(public_key, draft).unwrap();
        assert!(body.starts_with("v1."));
        assert!(body.len() <= 4096);
        let plain = open_feedback(&secret.to_bytes(), &body).unwrap();
        serde_json::from_slice(&plain).unwrap()
    }

    #[test]
    fn seals_and_opens() {
        let json = roundtrip(FeedbackDraft {
            category: "bug".into(),
            text: "翻页会卡住".into(),
            contact: "".into(),
            app_version: "0.1.0 (1)".into(),
            platform: "ios".into(),
            os_version: "iOS 18.2".into(),
        });
        assert_eq!(json["v"], 1);
        assert_eq!(json["category"], "bug");
        assert_eq!(json["text"], "翻页会卡住");
        assert_eq!(json["contact"], "");
        assert_eq!(json["platform"], "ios");
        assert!(json["sentAt"].as_u64().unwrap() > 0);
    }

    #[test]
    fn rejects_empty_long_and_a_bad_key() {
        let draft = FeedbackDraft {
            category: "idea".into(),
            text: "  ".into(),
            contact: "".into(),
            app_version: "0".into(),
            platform: "android".into(),
            os_version: "14".into(),
        };
        let secret = SecretKey::generate(&mut OsRng);
        let public_key = STANDARD.encode(secret.public_key().as_bytes());
        assert!(seal_feedback(public_key.clone(), draft).is_err());
        let long = FeedbackDraft {
            category: "idea".into(),
            text: "字".repeat(TEXT_MAX + 1),
            contact: "".into(),
            app_version: "0".into(),
            platform: "android".into(),
            os_version: "14".into(),
        };
        assert!(seal_feedback(public_key.clone(), long).is_err());
        let ok = FeedbackDraft {
            category: "other".into(),
            text: "字".repeat(TEXT_MAX),
            contact: "邮".repeat(CONTACT_MAX),
            app_version: "0.1.0 (1)".into(),
            platform: "android".into(),
            os_version: "Android 14".into(),
        };
        let body = seal_feedback(public_key, ok).unwrap();
        assert!(body.len() <= 4096);
        assert!(seal_feedback("not-a-key".into(), FeedbackDraft {
            category: "bug".into(),
            text: "hi".into(),
            contact: "".into(),
            app_version: "0".into(),
            platform: "ios".into(),
            os_version: "1".into(),
        }).is_err());
    }

    /// The box the app seals is the box PyNaCl (libsodium) opens, and the reverse.
    #[test]
    fn matches_libsodium() {
        let probe = std::process::Command::new("python3").arg("-c").arg("import nacl").status();
        if !probe.map(|s| s.success()).unwrap_or(false) {
            eprintln!("skip libsodium interop: pynacl is not installed");
            return;
        }
        let secret = SecretKey::generate(&mut OsRng);
        let public_key = STANDARD.encode(secret.public_key().as_bytes());
        let body = seal_feedback(public_key, FeedbackDraft {
            category: "bug".into(),
            text: "from rust".into(),
            contact: "".into(),
            app_version: "0".into(),
            platform: "test".into(),
            os_version: "test".into(),
        }).unwrap();
        let script = r#"
import base64, json, sys
from nacl.public import SealedBox, PrivateKey
secret, body = sys.argv[1], sys.argv[2]
sk = PrivateKey(base64.b64decode(secret))
plain = SealedBox(sk).decrypt(base64.b64decode(body.removeprefix("v1.")))
print(plain.decode())
back = SealedBox(sk.public_key).encrypt(b'{"v":1,"text":"from nacl"}')
print(base64.b64encode(back).decode())
"#;
        let out = std::process::Command::new("python3")
            .arg("-c")
            .arg(script)
            .arg(STANDARD.encode(secret.to_bytes()))
            .arg(&body)
            .output()
            .expect("python");
        assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
        let lines = String::from_utf8(out.stdout).unwrap();
        let (opened, sealed) = lines.trim().split_once('\n').unwrap();
        let json: serde_json::Value = serde_json::from_str(opened).unwrap();
        assert_eq!(json["text"], "from rust");
        let plain = open_feedback(&secret.to_bytes(), &format!("v1.{sealed}")).unwrap();
        assert_eq!(plain, br#"{"v":1,"text":"from nacl"}"#);
    }
}
