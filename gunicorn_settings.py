import os

bind = '0.0.0.0:' + str(os.getenv('PORT', 80))
proc_name = 'sekai-result-ocr'
workers = 1
