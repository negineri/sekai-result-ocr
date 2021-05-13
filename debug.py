import ocr_result
import sys

try:
    checker = ocr_result.ScoreResultChecker()
except ocr_result.OCRException as err:
    print(err)
    sys.exit(1)
data = ocr_result.loadfile("/workspace/tmp/0ce77671-7de4-46b3-b8b0-fc94bde1d59c.png", debug=True)
print(data.to_dict())
fix_data = checker.correct(data)
if fix_data is not None:
    print(fix_data.to_dict())
else:
    print("修正不可")
