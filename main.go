package main

import (
	"flag"
	"fmt"
	"image"
	"image/jpeg"
	_ "image/png"
	"os"
)

type (
	SubImager interface {
		SubImage(r image.Rectangle) image.Image
	}
	resultOCR struct {
		title      string
		difficulty string
		perfect    int
		great      int
		good       int
		bad        int
		miss       int
	}
)

func ocrResult(path string) (result *resultOCR, err error) {
	f, err := os.Open(path)
	if err != nil {
		fmt.Println("open:", err)
		return
	}
	defer f.Close()

	img, _, err := image.Decode(f)
	if err != nil {
		fmt.Println("decode:", err)
		return
	}

	rct := img.Bounds()
	w := float64(rct.Dx())
	h := float64(rct.Dy())
	var imCrop image.Image
	var imTitle image.Image
	xOrigin = 0
	yOrigin = 0
	if h/w > 0.5625 {
		hO := h
		h = w * 0.5625
		imCrop = img.(SubImager).SubImage(image.Rect(0, int((hO-h)/2), int(w), int(hO-h)/2+int(h)))
		imTitle = img.(SubImager).SubImage(image.Rect(int(w*0.081), 0, int(w*0.5), int(h*0.066)))
	} else {
		wO := w
		w = h * 1.7778
		imCrop = img.(SubImager).SubImage(image.Rect(int(wO-w)/2, 0, int(wO-w)/2+int(w), int(h)))
		imTitle = imCrop.(SubImager).SubImage(image.Rect(int(w*0.081), 0, int(w*0.5), int(h*0.066)))
		fmt.Printf("%g %d\n", wO, imCrop.Bounds().Dx())
	}

	//cimg := img.(SubImager).SubImage(image.Rect(50, 0, 150, 100))
	fso, err := os.Create("data/dst/out.jpg")
	if err != nil {
		fmt.Println("create:", err)
		return
	}
	defer fso.Close()
	jpeg.Encode(fso, imCrop, &jpeg.Options{Quality: 100})

	ftitle, err := os.Create("data/dst/title.jpg")
	if err != nil {
		fmt.Println("create:", err)
		return
	}
	defer ftitle.Close()
	jpeg.Encode(ftitle, imTitle, &jpeg.Options{Quality: 100})
	return
}

func main() {
	fmt.Println("Hello world!")
	flag.Parse()
	args := flag.Args()
	ocrResult(args[0])
}
