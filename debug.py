import ocr_result
import sys

try:
    checker = ocr_result.ScoreResultChecker()
except ocr_result.OCRException as err:
    print(err)
    sys.exit(1)
data = ocr_result.loadfile("data/src/image6.png", debug=True)
fix_data = checker.correct(data)
print(data.to_dict())
if fix_data is not None:
    print(fix_data.to_dict())
else:
    print("修正不可")
