using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using OpenCvSharp;
using OpenCvSharp4.Extensions;
using Tesseract;
using System.Web.UI;

namespace ImgeScan
{
    public partial class About : System.Web.UI.Page
    {
        static readonly Dictionary<string, string> categories = new Dictionary<string, string>
    {
        { "#7EB3C8", "SP Suite" },
        { "#A2ACCE", "CW Suite" },
        { "#CCD1E5", "CO Suite" },
        { "#B8E3E6", "N1 Suite" },
        { "#DAEFF2", "N2 Suite" },
        { "#FFFFFF", "W" },
        { "#F68933", "P1 Balcony" },
        { "#DFC3C3", "P2 Balcony" },
        { "#C6979A", "P3 Balcony" },
        { "#FED5B3", "V1 Balcony" },
        { "#D0A893", "V2 Balcony" },
        { "#EDDCD1", "V3 Balcony" },
        { "#9DA768", "04 OceanView" },
        { "#FFDD97", "05 OceanView" },
        { "#CBDBD5", "10 Inside" }
    };



        static List<CabinData> ExtractCabinNumbersAndCoords(string imagePath)
        {
            Mat image = Cv2.ImRead(imagePath);
            Mat grayImage = new Mat();
            Cv2.CvtColor(image, grayImage, ColorConversionCodes.BGR2GRAY);

            Mat thresholdImage = new Mat();
            Cv2.Threshold(grayImage, thresholdImage, 0, 255, ThresholdTypes.Binary | ThresholdTypes.Otsu);

            var cabinData = new List<CabinData>();

            using (var engine = new TesseractEngine(@"./tessdata", "eng", EngineMode.Default))
            {
                using (var img = ConvertMatToPix(thresholdImage))
                {
                    using (var page = engine.Process(img))
                    {
                        var text = page.GetText();
                        var iter = page.GetIterator();

                        iter.Begin();

                        do
                        {
                            if (iter.TryGetBoundingBox(PageIteratorLevel.Word, out var bounds))
                            {
                                var wordText = iter.GetText(PageIteratorLevel.Word);
                                if (int.TryParse(wordText, out int cabinNumber))
                                {
                                    var subMat = new Mat(image, new OpenCvSharp.Rect(bounds.X1, bounds.Y1, bounds.Width, bounds.Height));
                                    var category = CategorizeCabin(subMat);
                                    cabinData.Add(new CabinData
                                    {
                                        CabinNo = cabinNumber,
                                        Category = category.category,
                                        CabinTypeException = category.cabinTypeException,
                                        CoordinatesPoint = new System.Drawing.Point(bounds.X1, bounds.Y1)
                                    });
                                }
                            }
                        } while (iter.Next(PageIteratorLevel.Word));
                    }
                }
            }

            return cabinData;
        }

        static (string category, string cabinTypeException) CategorizeCabin(Mat cabinImage)
        {
            Mat resizedImage = new Mat();
            Cv2.Resize(cabinImage, resizedImage, new OpenCvSharp.Size(1, 1));

            var color = resizedImage.At<Vec3b>(0, 0);
            string avgColorHex = $"#{color.Item2:X2}{color.Item1:X2}{color.Item0:X2}";

            string category = categories.TryGetValue(avgColorHex, out string value) ? value : "Unknown";
            string cabinTypeException = "None";  // Placeholder, replace with actual logic if needed

            return (category, cabinTypeException);
        }

        static Pix ConvertMatToPix(Mat image)
        {
            Mat mat = new Mat(image);
            Bitmap bitmap = OpenCvSharp4.Extensions.BitmapConverter.ToMat(image);
            return PixConverter.ToPix(bitmap);
        }

        public class CabinData
        {
            public int CabinNo { get; set; }
            public string Category { get; set; }
            public string CabinTypeException { get; set; }
            public System.Drawing.Point CoordinatesPoint { get; set; }
            public string Coordinates => $"({CoordinatesPoint.X}, {CoordinatesPoint.Y})";
        }

    }

    }