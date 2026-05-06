import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import requests
import asyncio

api_key = "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"

async def send_otp_email(user_name: str, full_name: str, otp: str):
    # Configure API Key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = api_key

    # Initialize API client
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


    # Email content
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        subject="FitHub Account Verification",
        sender={"email": "noreply@fithub.com", "name": "fithub.com"},
        to=[{"email": user_name, "name": full_name}],
        html_content=f"""
            <html>
            <body>
            <p>Hi {full_name},</p>
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: "12px";
            ">
        <p>Your verification code is:</p>
        <h1 style="letter-spacing:8px;color:#E4FF4D;">{otp}</h1>
        <p>This OTP expires in <strong>15 minutes</strong>.</p>
        <p>If you did not create this account, ignore this email.</p>
            <p style="
                display: flex;
                flex-direction: column;
                align-items: left;
            ">Thank you,<br>FitHub Team</p>
            </div>
            </body>
            </html>
            """,
        )
    try:
        # Send email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("api_response>>",api_response)
    except ApiException as e:
        print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")


async def send_forget_email_verification(user_name: str, full_name: str, otp: str):
     # Configure API Key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = api_key

    # Initialize API client
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


    # Email content
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        subject="fithub - Reset Password",
        sender={"email": "noreply@fithub.com", "name": "fithub.com"},
        to=[{"email": user_name, "name": full_name}],
        html_content=f"""
            <html>
            <body>
            <p>Hi {full_name},</p>
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: "12px";
            ">
        <p>Your verification code is:</p>
        <h1 style="letter-spacing:8px;color:#E4FF4D;">{otp}</h1>
        <p>This OTP expires in <strong>15 minutes</strong>.</p>
        <p>If you did not create this account, ignore this email.</p>
            <p style="
                display: flex;
                flex-direction: column;
                align-items: left;
            ">Thank you,<br>FitHub Team</p>
            </div>
            </body>
            </html>
            """,
        )
    try:
        # Send email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("api_response>>",api_response)
    except ApiException as e:
        print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")


async def send_otp(user_name: str, companyName:str, otp: str, token: str):
    # Configure API Key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = api_key

    # Initialize API client
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    logo_url = "https://scontent.fcmb2-2.fna.fbcdn.net/v/t39.30808-1/453881977_122103855704447155_5427710283377777656_n.jpg?stp=dst-jpg_s200x200_tt6&_nc_cat=109&ccb=1-7&_nc_sid=2d3e12&_nc_eui2=AeENCYI-nHEqs2gI2PkxJM-F4_QUgqRv8FPj9BSCpG_wU8uh9ZGb2kBDRuALv_o350AWAqASKLPNtRFyEJB1b6QZ&_nc_ohc=sJicJ2MTWPIQ7kNvwHmd0qx&_nc_oc=AdkOPG_MuuyrAdwlL91HWJqUNcbgwBmKfIQkxXJkF4uATKF3q2MHDr_R_ErltOjweYw&_nc_zt=24&_nc_ht=scontent.fcmb2-2.fna&_nc_gid=HEjFazBm4ailzbEkQg0ovw&oh=00_AfTcUmfcKGOp4kuHy9Qmg7x7JgFXtZJszA-IYLMwfMXvpg&oe=68771584" 

    # Email content
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        subject="fithub.com Account Verification",
        sender={"email": "noreply@fithub.com", "name": "fithub.com"},
        to=[{"email": user_name, "name": companyName}],
        html_content=f"""
             <html>
            <body>
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: "12px";
            ">
             <p style="font-size: 12px; color: #555;">This is your Verification Code.  Don't Share your Code with anyone. </p>  <br/>
           <div style="
                text-decoration: none;
                font-weight: 700;
                font-size: 24px;
                color: #BE17FA;
                padding: 8px 24px;
                display: inline-block;
            ">{otp}</div>
            <p style="
                display: flex;
                flex-direction: column;
                align-items: left;
                margin-top: 40px;
                color: #999;
            ">Thank you,<br>- fithub.com Team -</p>
            </div>
            </body>
            </html>
            """,
        )
    try:
        # Send email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("api_response>>",api_response)
    except ApiException as e:
        print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")
