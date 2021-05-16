import ocr_result
import sys

try:
    checker = ocr_result.ScoreResultChecker()
except ocr_result.OCRException as err:
    print(err)
    sys.exit(1)
reader = ocr_result.ResultReader('data/tpls')
data = reader.loadfile("/workspace/tmp/6e2d8825-7390-4d42-b179-5e815ce76d67.png", debug=True)
print(data.to_dict())
fix_data = checker.correct(data)
if fix_data is not None:
    print(fix_data.to_dict())
else:
    print("修正不可")
