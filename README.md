# 🔐 Android-InsecureBankv2 – Security Hardening Project

**A comprehensive security assessment and mitigation project for a vulnerable mobile banking application.**

---

## 📌Overview

This project demonstrates a **full-cycle security engineering approach**:
- **Discovery** – Identify critical vulnerabilities in a mobile banking app.
- **Exploitation** – Prove the impact of each vulnerability using BurpSuite and ADB.
- **Remediation** – Implement secure coding practices and cryptographic improvements.
- **Verification** – Retest to confirm fixes are effective and functional.

🧰 Prerequisites
Kali Linux (or any Debian‑based Linux)
Genymotion (Android emulator) installed on Windows (or Kali)
BurpSuite installed on Windows (for intercepting traffic)
ADB installed on Kali (sudo apt install adb -y)
Python 3 and pip on Kali
---


## ⚠️ Vulnerabilities Found & Fixed

| # | Vulnerability | Severity | Location | Fix Applied |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Insecure Direct Object Reference (IDOR)** | Critical | `/dotransfer` | Added ownership check: `Account.query.filter(Account.account_number == from_acc, Account.user == user).first()` |
| 2 | **Broken Authorization (Password Hijacking)** | Critical | `/changepassword` | Enforced current password verification before allowing password change |
| 3 | **Hardcoded Cryptographic Key** | High | `CryptoClass.java` | Replaced hardcoded key with **Android Keystore** (device-unique, hardware-backed) |
| 4 | **SQL Injection** | ✅ NOT VULNERABLE | `/getaccounts` | Uses SQLAlchemy ORM (parameterized queries) – securely implemented by original developer |
-----
Clone the Original InsecureBankv2 Project
Open a terminal on Kali and run:
       
        cd ~
        git clone https://github.com/dineshshetty/Android-InsecureBankv2.git InsecureBankv2-Original
        cd InsecureBankv2-Original
        cd AndroLabServer
        pip3 install flask flask-sqlalchemy sqlalchemy pycryptodome
  #start server
        
        python3 app.py
🚀 Running the Application

### 1. Start the Android Emulator

- Launch **Genymotion** and start your virtual device.
- Open the **InsecureBankv2** application.
  - If you're using the provided APK, it should already be installed.
  - Otherwise, install the APK before proceeding.

---

### 2. Configure the Server Connection

Inside the application:

1. Open **Settings** (gear icon or menu).
2. Set the server URL to:

```text
http://<KALI_IP>:8888
```

Replace `<KALI_IP>` with the IP address of your Kali Linux machine.

To find your Kali IP:

```bash
ip a
```
Configure Burp Suite Proxy

### On Windows

1. Launch **Burp Suite**.
2. Go to:

```
Proxy → Options → Proxy Listeners
```

3. Ensure a listener is running on:

```text
127.0.0.1:8082
```

---

### Configure the Emulator Proxy

In Genymotion:

1. Open **Wi-Fi Settings**.
2. Edit the connected network.
3. Set the proxy to **Manual**.
4. Configure:

| Setting | Value |
|---------|-------|
| Proxy Host | Windows Host IP |
| Proxy Port | 8082 |

> Replace **Windows Host IP** with the IP address of your Windows machine that is reachable from the emulator.

---



## 🛠️ Fix Details

### Fix 1 – IDOR (Money Transfer)
Replace the entire /dotransfer function with this secure implementation

    @app.route('/dotransfer', methods=['POST'])
    def dotransfer():
        user = request.form['username']
        password = request.form['password']
        from_acc = request.form['from_acc']
        to_acc = request.form['to_acc']
        amount_str = request.form['amount']
    
    # 1. Validate credentials
    u = User.query.filter(User.username == user).first()
    if not u or u.password != password:
        return jsonify({"message": "Invalid credentials", "status": "failed"})
    
    # 2. Validate ownership of source account (KILLS IDOR)
    account = Account.query.filter(Account.account_number == from_acc, Account.user == user).first()
    if not account:
        return jsonify({"message": "Invalid transaction request", "status": "failed"})
    
    # 3. Fetch the actual account objects for both accounts
    from_account = Account.query.filter(Account.account_number == from_acc).first()
    to_account = Account.query.filter(Account.account_number == to_acc).first()
    
    # 4. Validate that BOTH accounts exist in the system
    if not from_account or not to_account:
        return jsonify({"message": "Invalid accounts provided", "status": "failed"})
    
    # 5. Check sufficient balance
    if from_account.balance < int(amount_str):
        return jsonify({"message": "Insufficient balance", "status": "failed"})
    
    # 6. Perform the transfer
    from_account.balance -= int(amount_str)
    to_account.balance += int(amount_str)
    db_session.commit()
    
    return jsonify({"message": "Success", "from": from_acc, "to": to_acc, "amount": amount_str})

Fix 2: Broken Authorization (Password Hijacking)

    @app.route('/changepassword', methods=['POST'])
    def changePassword():
        user = request.form.get('username')
        old_pass = request.form.get('oldPassword')
        new_pass = request.form.get('newpassword')
    
    if not user or not old_pass or not new_pass:
        return jsonify({"message": "Missing required fields", "status": "failed"}), 400
    
    u = User.query.filter(User.username == user).first()
    if not u:
        return jsonify({"message": "User does not exist", "status": "failed"}), 404
    
    if u.password != old_pass:
        return jsonify({"message": "Incorrect current password", "status": "failed"}), 401
    
    u.password = new_pass
    db_session.commit()
    return jsonify({"message": "Password changed successfully", "status": "success"}), 200

Fix 3: Hardcoded Cryptographic Key

    package com.android.insecurebankv2;
    
    import android.security.keystore.KeyGenParameterSpec;
    import android.security.keystore.KeyProperties;
    import android.util.Base64;
    
    import java.security.KeyStore;
    import java.security.SecureRandom;
    import javax.crypto.Cipher;
    import javax.crypto.KeyGenerator;
    import javax.crypto.SecretKey;
    import javax.crypto.spec.IvParameterSpec;
    
    public class CryptoClass {

    private static final String KEY_ALIAS = "BankSecureKey";
    private static final String TRANSFORMATION = "AES/CBC/PKCS5Padding";

    private static SecretKey getSecretKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);

        if (!keyStore.containsAlias(KEY_ALIAS)) {
            KeyGenerator keyGen = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            keyGen.init(new KeyGenParameterSpec.Builder(KEY_ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(KeyProperties.BLOCK_MODE_CBC)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_PKCS7)
                    .setUserAuthenticationRequired(false)
                    .build());
            keyGen.generateKey();
        }
        return (SecretKey) keyStore.getKey(KEY_ALIAS, null);
    }

    public String aesEncryptedString(String plainText) throws Exception {
        SecretKey key = getSecretKey();
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        byte[] iv = new byte[16];
        new SecureRandom().nextBytes(iv);
        IvParameterSpec ivSpec = new IvParameterSpec(iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, ivSpec);
        byte[] cipherText = cipher.doFinal(plainText.getBytes("UTF-8"));
        byte[] combined = new byte[iv.length + cipherText.length];
        System.arraycopy(iv, 0, combined, 0, iv.length);
        System.arraycopy(cipherText, 0, combined, iv.length, cipherText.length);
        return Base64.encodeToString(combined, Base64.DEFAULT);
    }

    public String aesDeccryptedString(String base64Text) throws Exception {
        byte[] combined = Base64.decode(base64Text, Base64.DEFAULT);
        byte[] iv = new byte[16];
        System.arraycopy(combined, 0, iv, 0, 16);
        byte[] cipherText = new byte[combined.length - 16];
        System.arraycopy(combined, 16, cipherText, 0, cipherText.length);

        SecretKey key = getSecretKey();
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        IvParameterSpec ivSpec = new IvParameterSpec(iv);
        cipher.init(Cipher.DECRYPT_MODE, key, ivSpec);
        byte[] plainText = cipher.doFinal(cipherText);
        return new String(plainText, "UTF-8");
    }
    }


     Acknowledgments
Original project: https://github.com/dineshshetty/Android-InsecureBankv2.git by Dinesh Shetty

Built for educational purposes to demonstrate real-world security engineering.







