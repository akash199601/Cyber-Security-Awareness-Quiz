/****** Script for SelectTopNRows command from SSMS  ******/
SELECT TOP (1000) [id]
      ,[question_text]
  FROM [Sonata_Cyber_Quiz].[dbo].[Quiz_question]


INSERT INTO Quiz_question (question_text) VALUES 
('What is the main function of a firewall?'),
('What is malware?'),
('Why should you update your software regularly?'),
('What is a strong password practice?'),
('What does "phishing" mean?'),
('What is two-factor authentication (2FA)?'),
('What should you do if you receive an email asking for personal information?'),
('What is identity theft?'),
('How can you keep your online accounts secure?'),
('What is a common indicator of a secure website?'),
('What is a common feature of spam emails?'),
('What should you do if you receive a suspicious text message?'),
('What is a phishing email?'),
('How can you identify spam emails?'),
('What is a good practice for dealing with spam emails?'),
('What does "data privacy" refer to?'),
('Why is it important to use strong passwords?'),
('What is a privacy policy?'),
('What should you do before providing personal information on a website?'),
('How can you protect your data privacy online?');




INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(1, 'a) To protect against viruses', 0),
(1, 'b) To block unauthorized access to a network', 1),
(1, 'c) To speed up your computer', 0),
(1, 'd) To clean up files', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(2, 'a) A type of computer game', 0),
(2, 'b) Software designed to damage or disrupt a system', 1),
(2, 'c) A software update', 0),
(2, 'd) A secure network connection', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(3, 'a) To add new features', 0),
(3, 'b) To fix security vulnerabilities', 1),
(3, 'c) To change the interface', 0),
(3, 'd) To increase storage space', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(4, 'a) Using a combination of letters, numbers, and symbols', 1),
(4, 'b) Using your name or birthdate', 0),
(4, 'c) Using the same password for multiple accounts', 0),
(4, 'd) Sharing your password with friends', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(5, 'a) Fishing for information by pretending to be someone else', 1),
(5, 'b) A type of software update', 0),
(5, 'c) A method of improving computer speed', 0),
(5, 'd) A way to back up data', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(6, 'a) A method that requires a second step to verify identity', 1),
(6, 'b) A type of password', 0),
(6, 'c) A way to store passwords', 0),
(6, 'd) A computer program', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(7, 'a) Reply with your details', 0),
(7, 'b) Ignore and delete the email', 1),
(7, 'c) Forward it to friends', 0),
(7, 'd) Click on any links provided', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(8, 'a) Losing your identity card', 0),
(8, 'b) When someone uses your personal information without permission', 1),
(8, 'c) A method of changing your password', 0),
(8, 'd) A type of virus', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(9, 'a) By using unique passwords for each account', 1),
(9, 'b) By sharing passwords with colleagues', 0),
(9, 'c) By using the same password for all accounts', 0),
(9, 'd) By ignoring security updates', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(10, 'a) A lock icon in the address bar', 1),
(10, 'b) A warning message', 0),
(10, 'c) A colorful banner', 0),
(10, 'd) Pop-up advertisements', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(11, 'a) Contains poor grammar and spelling mistakes', 1),
(11, 'b) Comes from trusted contacts only', 0),
(11, 'c) Has no subject line', 0),
(11, 'd) Is well-written and formal', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(12, 'a) Ignore and delete the message', 1),
(12, 'b) Reply with personal information', 0),
(12, 'c) Forward it to your friends', 0),
(12, 'd) Click on the links', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(13, 'a) An email designed to trick you into giving up personal information', 1),
(13, 'b) A newsletter', 0),
(13, 'c) A software update notification', 0),
(13, 'd) A promotional offer', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(14, 'a) Suspicious sender address and subject', 1),
(14, 'b) Sent from a known contact', 0),
(14, 'c) Contains many graphics', 0),
(14, 'd) Contains official company logos', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(15, 'a) Mark them as spam or junk', 1),
(15, 'b) Respond to ask for removal from the list', 0),
(15, 'c) Forward them to friends', 0),
(15, 'd) Open all the links inside', 0);


INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(16, 'a) Controlling how personal information is collected and used', 1),
(16, 'b) Hiding data from the government', 0),
(16, 'c) Sharing data with everyone', 0),
(16, 'd) Erasing data from your computer', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(17, 'a) To prevent unauthorized access to personal information', 1),
(17, 'b) To make your accounts easier to remember', 0),
(17, 'c) To help others guess your password', 0),
(17, 'd) To use the same password for all accounts', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(18, 'a) A legal document explaining how your data will be used', 1),
(18, 'b) A pop-up message', 0),
(18, 'c) An advertisement', 0),
(18, 'd) A notification about software updates', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(19, 'a) Check the website’s privacy policy', 1),
(19, 'b) Share all your details immediately', 0),
(19, 'c) Provide a fake name', 0),
(19, 'd) Ignore the security warnings', 0);

INSERT INTO Quiz_option (question_id, option_text, is_correct) VALUES
(20, 'a) By using strong passwords and secure websites', 1),
(20, 'b) By sharing your passwords with trusted people', 0),
(20, 'c) By ignoring privacy settings', 0),
(20, 'd) By saving passwords in an open document', 0);
