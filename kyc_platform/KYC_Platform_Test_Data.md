# KYC Platform Test Cases Reference Document

This document contains the structured test data for the 8 core KYC scenarios. 
An Excel-compatible version of this dataset has been saved in your workspace at [KYC_Platform_Test_Data.csv](file:///c:/Users/juvvi/Downloads/kyc_platform/KYC_Platform_Test_Data.csv).

---

## 📊 Summary Table

| Case ID | Full Legal Name | Target Decision | Risk Band | Document Type | Document Number | Key Risk Indicator / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Case 1** | Priya Sharma | `APPROVE` | LOW | PAN | `ABCPS8821P` | Clean profile, Software Engineer, auto-approved. |
| **Case 2** | Rahul Mehta | `REVIEW` | MEDIUM | PAN | `ABCPM8821M` | Watchlist match: PEP List. |
| **Case 3** | Kevin Ross | `ESCALATE` | CRITICAL | PAN | `ABCPK8821K` | Watchlist match: Sanctions list. Student with high Crypto income. |
| **Case 4** | Sarah Jenkins | `APPROVE` | LOW | PASSPORT | `UK992341A` | Safe international profile, Consultant. |
| **Case 5** | Marcus Vance | `REVIEW` | MEDIUM | PASSPORT | `US8812349` | High-risk industry (Crypto) & high Crypto income. |
| **Case 6** | Rajendra Kumar Singh | `REVIEW` | MEDIUM | PAN | `ABCRK1234S` | Watchlist match: PEP list. |
| **Case 7** | Dmitri Volkov | `ESCALATE` | CRITICAL | PASSPORT | `RU9981245` | Watchlist match: OFAC Sanctions list. |
| **Case 8** | David Miller | `ESCALATE` | HIGH | PAN | `INVALID_PAN_123` | Fails PAN format validation. Authenticity set to False. |

---

## 📝 Individual Case Specifications

### Case 1: Priya Sharma
* **Expected Result:** `APPROVE` (Score < 45)
* **Form Inputs:**
  * **Full Legal Name:** `Priya Sharma`
  * **Date of Birth:** `1990-05-14`
  * **Nationality:** `Indian`
  * **Email:** `priya.sharma@example.com`
  * **Phone:** `+91 95025 37956`
  * **Document Type:** `PAN`
  * **Document Number:** `ABCPS8821P`
  * **Occupation:** `Software Engineer`
  * **Annual Income:** `1200000`
  * **Source of Funds:** `Salary`
  * **Address:** `4-6, Cheemalapalle, Atchuthapuram, Anakapalle, AP, India`
  * **Document File:** [priya_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/priya_pan.png)
  * **Selfie File:** [priya_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/priya_pic.png)

### Case 2: Rahul Mehta
* **Expected Result:** `REVIEW` (Score >= 45 or Forced PEP Review)
* **Form Inputs:**
  * **Full Legal Name:** `Rahul Mehta`
  * **Date of Birth:** `1985-11-03`
  * **Nationality:** `Indian`
  * **Email:** `rahul.mehta@example.com`
  * **Phone:** `+91 98234 56789`
  * **Document Type:** `PAN`
  * **Document Number:** `ABCPM8821M`
  * **Occupation:** `Business Owner`
  * **Annual Income:** `5500000`
  * **Source of Funds:** `Business`
  * **Address:** `Flat 402, Sunset Towers, Bandra West, Mumbai, MH, India`
  * **Document File:** [rahul_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/rahul_pan.png)
  * **Selfie File:** [Rahul_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/Rahul_pic.png)

### Case 3: Kevin Ross
* **Expected Result:** `ESCALATE` (Watchlist Sanctions Hit)
* **Form Inputs:**
  * **Full Legal Name:** `Kevin Ross`
  * **Date of Birth:** `2005-03-22`
  * **Nationality:** `Nigerian`
  * **Email:** `kevin.ross@example.com`
  * **Phone:** `+234 803 123 4567`
  * **Document Type:** `PAN`
  * **Document Number:** `ABCPK8821K`
  * **Occupation:** `Student`
  * **Annual Income:** `50000000`
  * **Source of Funds:** `Crypto`
  * **Address:** `12 Alausa Way, Ikeja, Lagos, Nigeria`
  * **Document File:** [kevin_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/kevin_pan.png)
  * **Selfie File:** [kevin_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/kevin_pic.png)

### Case 4: Sarah Jenkins
* **Expected Result:** `APPROVE` (Score < 45)
* **Form Inputs:**
  * **Full Legal Name:** `Sarah Jenkins`
  * **Date of Birth:** `1982-08-19`
  * **Nationality:** `British`
  * **Email:** `sarah.jenkins@example.com`
  * **Phone:** `+44 7911 123456`
  * **Document Type:** `PASSPORT`
  * **Document Number:** `UK992341A`
  * **Occupation:** `Management Consultant`
  * **Annual Income:** `4500000`
  * **Source of Funds:** `Salary`
  * **Address:** `14 High Street, Richmond, London, TW9 1EZ, United Kingdom`
  * **Document File:** [sarah_jenkins_passport.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/sarah_jenkins_passport.png)
  * **Selfie File:** [sarah_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/sarah_pic.png)

### Case 5: Marcus Vance
* **Expected Result:** `REVIEW` (Score >= 45)
* **Form Inputs:**
  * **Full Legal Name:** `Marcus Vance`
  * **Date of Birth:** `1978-12-05`
  * **Nationality:** `American`
  * **Email:** `marcus.vance@example.com`
  * **Phone:** `+1 305 555 0199`
  * **Document Type:** `PASSPORT`
  * **Document Number:** `US8812349`
  * **Occupation:** `Crypto Fund Manager`
  * **Annual Income:** `25000000`
  * **Source of Funds:** `Crypto`
  * **Address:** `890 Ocean Drive, Miami, FL 33139, USA`
  * **Document File:** [marcus_vance_passport.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/marcus_vance_passport.png)
  * **Selfie File:** [marcus_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/marcus_pic.png)

### Case 6: Rajendra Kumar Singh
* **Expected Result:** `REVIEW` (Score >= 45 or Forced PEP Review)
* **Form Inputs:**
  * **Full Legal Name:** `Rajendra Kumar Singh`
  * **Date of Birth:** `1968-04-12`
  * **Nationality:** `Indian`
  * **Email:** `rajendra.singh@example.com`
  * **Phone:** `+91 99123 45678`
  * **Document Type:** `PAN`
  * **Document Number:** `ABCRK1234S`
  * **Occupation:** `Business Consultant`
  * **Annual Income:** `3500000`
  * **Source of Funds:** `Investments`
  * **Address:** `12, Parliament Street, New Delhi, 110001, Delhi, India`
  * **Document File:** [rajendra_singh_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/rajendra_singh_pan.png)
  * **Selfie File:** [rajendra_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/rajendra_pic.png)

### Case 7: Dmitri Volkov
* **Expected Result:** `ESCALATE` (Watchlist Sanctions Hit)
* **Form Inputs:**
  * **Full Legal Name:** `Dmitri Volkov`
  * **Date of Birth:** `1980-07-24`
  * **Nationality:** `Russian`
  * **Email:** `dmitri.volkov@example.com`
  * **Phone:** `+7 495 123-45-67`
  * **Document Type:** `PASSPORT`
  * **Document Number:** `RU9981245`
  * **Occupation:** `Entrepreneur`
  * **Annual Income:** `8500000`
  * **Source of Funds:** `Business`
  * **Address:** `10 Tverskaya Street, Moscow, 125009, Russia`
  * **Document File:** [dmitri_volkov_passport.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/dmitri_volkov_passport.png)
  * **Selfie File:** [dmitri_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/dmitri_pic.png)

### Case 8: David Miller
* **Expected Result:** `ESCALATE` (Invalid PAN Format)
* **Form Inputs:**
  * **Full Legal Name:** `David Miller`
  * **Date of Birth:** `1993-10-15`
  * **Nationality:** `American`
  * **Email:** `david.miller@example.com`
  * **Phone:** `+1 212 555 0144`
  * **Document Type:** `PAN`
  * **Document Number:** `INVALID_PAN_123`
  * **Occupation:** `Architect`
  * **Annual Income:** `2000000`
  * **Source of Funds:** `Salary`
  * **Address:** `456 Broadway, New York, NY 10012, USA`
  * **Document File:** [david_miller_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/david_miller_pan.png)
  * **Selfie File:** [david_miller_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/david_miller_pic.png)

---

## 🖼️ Document & Selfie Assets for Testing

The generated mock identity document files and selfie photos are stored in the `demo_assets/` folder of your project workspace.

### Original Case Assets (Cases 1 - 3):
* **Priya Sharma (Case 1)**:
  * **Document:** [priya_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/priya_pan.png)
  * **Selfie:** [priya_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/priya_pic.png)
* **Rahul Mehta (Case 2)**:
  * **Document:** [rahul_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/rahul_pan.png)
  * **Selfie:** [Rahul_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/Rahul_pic.png)
* **Kevin Ross (Case 3)**:
  * **Document:** [kevin_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/kevin_pan.png)
  * **Selfie:** [kevin_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/kevin_pic.png)

### New Case Assets (Cases 4 - 8):
* **Sarah Jenkins (Case 4)**:
  * **Document:** [sarah_jenkins_passport.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/sarah_jenkins_passport.png)
  * **Selfie:** [sarah_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/sarah_pic.png)
* **Marcus Vance (Case 5)**:
  * **Document:** [marcus_vance_passport.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/marcus_vance_passport.png)
  * **Selfie:** [marcus_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/marcus_pic.png)
* **Rajendra Kumar Singh (Case 6)**:
  * **Document:** [rajendra_singh_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/rajendra_singh_pan.png)
  * **Selfie:** [rajendra_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/rajendra_pic.png)
* **Dmitri Volkov (Case 7)**:
  * **Document:** [dmitri_volkov_passport.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/dmitri_volkov_passport.png)
  * **Selfie:** [dmitri_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/dmitri_pic.png)
* **David Miller (Case 8)**:
  * **Document:** [david_miller_pan.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/david_miller_pan.png)
  * **Selfie:** [david_miller_pic.png](file:///c:/Users/juvvi/Downloads/kyc_platform/demo_assets/david_miller_pic.png)
