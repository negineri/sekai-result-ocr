import os

bind = '127.0.0.1:' + str(os.getenv('PORT', 80))
proc_name = 'sekai-result-ocr'
workers = 1
