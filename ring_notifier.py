# Importing for image capture and processing
import cv2 as cv
from datetime import datetime
import time
import numpy as np
import os
import threading
import customtkinter as ctk
import threading

# Importing for sending emails:
import base64
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

# Importing for refresh token retrieval automation
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from undetected_chromedriver import Chrome

class SmartRingNotifier:

    def __init__(self, root):
        self.root = root
        self.root.title("Smart Ring Notifier")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        #---------------------------------------------------GUI Elements----------------------------------------------------------------------

        # The capture time interval ka slider
        self.label_interval = ctk.CTkLabel(root, text="Capture Interval (seconds):")
        self.label_interval.pack(pady=10)

        self.interval_var = ctk.IntVar(value=20)
        self.interval_slider = ctk.CTkSlider(root, from_=1, to=60, variable=self.interval_var)
        self.interval_slider.pack(pady=0)

        self.label_interval_value = ctk.CTkLabel(root, textvariable=self.interval_var)
        self.label_interval_value.pack(pady=2)
       
        # Recipient email box
        self.email_frame = ctk.CTkFrame(root)
        self.email_frame.pack(pady=10, padx=10, fill=ctk.X)

        self.label_email = ctk.CTkLabel(self.email_frame, text="Recipient Email:")
        self.label_email.pack(side=ctk.LEFT, padx=5)

        self.entry_email = ctk.CTkEntry(self.email_frame, width=200, placeholder_text="example@example.com")
        self.entry_email.pack(side=ctk.LEFT, padx=5, expand=True, fill=ctk.X)

        # Start and stop buttons
        self.button_start = ctk.CTkButton(root, text="Start", command=self.start_capture)
        self.button_start.pack(pady=10)

        self.button_stop = ctk.CTkButton(root, text="Stop", command=self.stop_capture, state=ctk.DISABLED)
        self.button_stop.pack(pady=10)

       
        # Link if refresh token has been expired
        self.link_label = ctk.CTkLabel(root, text="Click here if the refresh token has been expired", fg_color="red", cursor="hand2")
        self.link_label.pack(pady=10)
        self.link_label.bind("<Button-1>", lambda e: self.refresh_token_with_selenium())

        self.running = False
        self.capture_thread = None
        self.stop_event = threading.Event() # This is a flag that we'll set to 1 when we need to stop the image capturing

#------------------------------------------------------Processing-----------------------------------------------------------------------------

    def are_images_same(self, img1, img2):
        img1 = cv.cvtColor(img1, cv.COLOR_BGR2GRAY)
        img2 = cv.cvtColor(img2, cv.COLOR_BGR2GRAY)
        mse = np.mean(cv.subtract(img1, img2) ** 2)
        max_mse = 255 ** 2
        return mse / max_mse < 0.0001   # Needs to be revaluated according to the actual telephone photos using trial and error

    def transform(self, img):   # According to the camera placement as shared by sir in the telephone photograph
        width, height = 640, 480

        pts1 = np.float32([[63, 292], [454, 210], [47, 475], [525, 381]])
        pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
        matrix = cv.getPerspectiveTransform(pts1, pts2)
        imgOut = cv.warpPerspective(img, matrix, (width, height))
        imgOut = cv.rotate(imgOut, cv.ROTATE_180)
        imgOut = cv.subtract(imgOut, np.array([150.0]))
        imgOut = cv.addWeighted(imgOut, 3, np.zeros(imgOut.shape, imgOut.dtype), 0, 2)

        return imgOut

#----------------------------------------------------Image capturing------------------------------------------------------------------------------
   
    def capture_images(self, time_interval_in_seconds):

        vid = cv.VideoCapture(0)

        if not vid.isOpened():
            print("Could not open webcam")
            return
       
        last_capture_time = time.time()
        success, prev = vid.read()
        prev = self.transform(prev) # Transform to compare only the display part of the telephone receiver

        if not success:
            print("Error encountered. Can't read from webcam")
            return
       
        while success and not self.stop_event.is_set():
            success, current_og = vid.read()
            current = self.transform(current_og) # Transform to compare only the display part of the telephone receiver

            if not success:
                print("Error encountered. Can't read from webcam")
                break

            cv.imshow("Webcam", current_og)

            if cv.waitKey(1) & 0xFF == ord('q'):
                break

            if time.time() - last_capture_time >= time_interval_in_seconds:
                if not self.are_images_same(prev, current):
                    timestamp = datetime.now().strftime(r"%Y%m%d_%H%M%S")
                    filekanaam = f"image_{timestamp}.jpg"
                    cv.imwrite(filekanaam, current)
                    print(f"Change detected. Therefore, image captured at {datetime.now()}.")
                    self.send_email(filekanaam)

                elif self.are_images_same(prev, current):
                    print("No change detected.")

                last_capture_time = time.time()

        vid.release()
        cv.destroyAllWindows()


    def start_capture(self):
        self.running = True
        self.button_start.configure(state=ctk.DISABLED)
        self.button_stop.configure(state=ctk.NORMAL)
        interval = int(self.interval_slider.get())
        self.capture_thread = threading.Thread(target=self.capture_images, args=(interval,))
        self.capture_thread.start()


    def stop_capture(self):
        self.running = False
        self.button_start.configure(state=ctk.NORMAL)
        self.button_stop.configure(state=ctk.DISABLED)
        self.stop_event.set()
        if self.capture_thread:
            self.capture_thread.join()
#------------------------------------------------------Loading refresh token from file----------------------------------------------------------

    def load_refresh_token(self):
        try:
            with open("refresh_token.txt", "r") as file:
                return file.read().strip()
           
        except FileNotFoundError:
            return None

#--------------------------------------------------------------Email sending---------------------------------------------------------------------

    def send_email(self, image_path):
        refresh_token = self.load_refresh_token()

        client_id = "the client id"
        client_secret = "client secret"
        token_uri = "https://oauth2.googleapis.com/token"

        creds = Credentials(
            None,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build('gmail', 'v1', credentials=creds)
        message = MIMEMultipart()
        message['to'] = self.entry_email.get()
        message['subject'] = "Your telephone is ringing"
        text = MIMEText(f"Hello, your telephone ring was detected at {datetime.now()}.")
        message.attach(text)

        with open(image_path, 'rb') as file:
            image = MIMEImage(file.read(), name=os.path.basename(image_path))

        message.attach(image)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            print("Email sent successfully!")
            os.remove(image_path)

        except Exception as e:
            print("Failed to send email:", e)

   

#-------------------------------------------------------Automation for refresh token retrieval-----------------------------------------------------
   
    def refresh_token_with_selenium(self):
        driver = Chrome(use_subprocess=True)
       
        def click_by_xpath(driver,xpath):
            WebDriverWait(driver,10).until(EC.visibility_of_element_located((By.XPATH,xpath)))
            a = driver.find_element(By.XPATH,xpath)
            ActionChains(driver).click(a).perform()
           
           
        def sendkeys_by_xpath(driver,xpath,keys):
            WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,xpath)))
            a = driver.find_element(By.XPATH,xpath)
            ActionChains(driver).send_keys_to_element(a,keys).perform()


        def login(driver): # For gmail login
            time.sleep(2)
            WebDriverWait(driver,20).until(EC.visibility_of_element_located((By.ID,"identifierId"))).send_keys("email id")
            ActionChains(driver).send_keys(Keys.RETURN).perform()
            time.sleep(2)
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, 'Passwd'))).send_keys("email password")
            ActionChains(driver).send_keys(Keys.RETURN).perform()

        try:
            #Open OAuth Playground
            driver.get("https://developers.google.com/oauthplayground/")

            # enter the mail api
            sendkeys_by_xpath(driver,"/html/body/div[5]/div[1]/div[1]/div/div/div/input","https://mail.google.com")

            # Settings open kro and use own oauth creds
            click_by_xpath(driver,"/html/body/div[4]/div[2]/div[3]/a")
            click_by_xpath(driver,"/html/body/div[4]/div[2]/div[3]/div/div/div[4]/input")
            sendkeys_by_xpath(driver,"/html/body/div[4]/div[2]/div[3]/div/div/div[5]/input","658025783945-q4859g2o8r4td3a6k6sf6kettme8pc3i.apps.googleusercontent.com")
            sendkeys_by_xpath(driver,"/html/body/div[4]/div[2]/div[3]/div/div/div[5]/div/input","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")
            click_by_xpath(driver,"/html/body/div[5]/div[1]/div[1]/div/div/div/div/button")

            # Step 3: Log into Gmail account
            login(driver)
           
            # google problems
            click_by_xpath(driver,"/html/body/div[1]/div[1]/a")
            click_by_xpath(driver,"/html/body/div[1]/div[2]/p[2]/a")
            click_by_xpath(driver,"/html/body/div[1]/div[1]/div[2]/div/div/div[3]/div/div[1]/div[2]/div/div/button/div[3]")
           
           
            # Step 4: Exchange authorization code for tokens
            click_by_xpath(driver,"/html/body/div[5]/div[1]/div[2]/h3")
            click_by_xpath(driver,"/html/body/div[5]/div[1]/div[2]/div/div/div[1]/button")
            time.sleep(3)  # Wait for the tokens to exchange

            # Get the new refresh token
            new_refresh_token_element = WebDriverWait(driver, 100).until(EC.visibility_of_element_located((By.ID,"refresh_token")))
            new_refresh_token = new_refresh_token_element.get_attribute("value")

            #Save the new refresh token to file
            with open("refresh_token.txt", "w") as file:
                file.write(new_refresh_token)

            print("New refresh token written to file. Please start the image capturing again")

        finally:
                driver.quit()    # Close the WebDriver session

#-------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    root = ctk.CTk()
    app = SmartRingNotifier(root)
    root.mainloop()
