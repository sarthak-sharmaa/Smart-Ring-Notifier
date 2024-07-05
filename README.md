# Smart-Ring-Notifier
The Smart Ring Notifier detects when a landline telephone with an LCD display is ringing and sends an email notification with an image attachment. It uses OpenCV for image processing, customtkinter for the GUI, and the Gmail API for email notifications. Selenium automates the retrieval of a new OAuth2 refresh token if the existing one expires.
## Features

- Detects changes in the LCD display of a landline telephone.
- Sends an email notification with an image attachment when a ring is detected.
- Provides a customtkinter GUI for user interaction.
- Automates the retrieval of a new OAuth2 refresh token using Selenium.

## Installation

### Prerequisites

- Python 3.10 or later
- Google Chrome
- Undetected ChromeDriver matching your Chrome version

- ## Code Overview

### Image Capturing

The `capture_images` method captures images from the webcam at regular intervals and checks for changes in the LCD display of the telephone. If a change is detected, an image is saved, and an email notification is sent.

### Email Sending

The `send_email` method uses the Gmail API to send an email with the captured image attached. It handles the OAuth2 authentication process and refreshes the token if necessary.

### Token Refresh Automation

The `refresh_token_with_selenium` method automates the process of retrieving a new OAuth2 refresh token using Selenium. This is triggered if the existing token expires.

### Main Function

The `__main__` function initializes the customtkinter GUI and starts the application.

### Scope

- The project focuses on developing a software solution using OpenCV for image detection and OAuth2 for sending email notifications.
- The solution is intended for use only with landline telephones that have an LCD display.
- The project demonstrates the integration of image processing and email notification systems.

### Limitations

- The system relies on a clear line of sight to the telephone's LCD display.
- Environmental factors such as lighting conditions can affect image detection accuracy.
- The solution assumes the availability of an internet connection for sending email notifications.

## GUI 
![ring](https://github.com/sarthak-sharmaa/Smart-Ring-Notifier/assets/147803893/2555922e-01e0-48d9-8b80-f39bc528db61)

