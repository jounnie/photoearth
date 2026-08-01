package com.photoearth.support;

import org.apache.commons.imaging.formats.jpeg.exif.ExifRewriter;
import org.apache.commons.imaging.formats.tiff.constants.ExifTagConstants;
import org.apache.commons.imaging.formats.tiff.constants.TiffTagConstants;
import org.apache.commons.imaging.formats.tiff.write.TiffOutputDirectory;
import org.apache.commons.imaging.formats.tiff.write.TiffOutputSet;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

/** Java analog of backend/tests/conftest.py::make_jpeg + tests/helpers.py::to_dms. */
public final class JpegFixtures {

    private JpegFixtures() {
    }

    public static byte[] plainJpeg() throws IOException {
        return encode(blankImage());
    }

    public static byte[] jpegWithGps(double lat, double lng) throws Exception {
        byte[] plain = plainJpeg();
        TiffOutputSet outputSet = new TiffOutputSet();
        outputSet.setGpsInDegrees(lng, lat);

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        new ExifRewriter().updateExifMetadataLossless(plain, out, outputSet);
        return out.toByteArray();
    }

    public static byte[] jpegWithDateTimeOriginal(String rawExifDate) throws Exception {
        return jpegWithDateTag(ExifTagConstants.EXIF_TAG_DATE_TIME_ORIGINAL, true, rawExifDate);
    }

    public static byte[] jpegWithDateTime(String rawExifDate) throws Exception {
        return jpegWithDateTag(TiffTagConstants.TIFF_TAG_DATE_TIME, false, rawExifDate);
    }

    public static byte[] jpegWithBothDateTags(String dateTimeOriginal, String dateTime) throws Exception {
        byte[] plain = plainJpeg();
        TiffOutputSet outputSet = new TiffOutputSet();
        outputSet.getOrCreateExifDirectory().add(ExifTagConstants.EXIF_TAG_DATE_TIME_ORIGINAL, dateTimeOriginal);
        outputSet.getOrCreateRootDirectory().add(TiffTagConstants.TIFF_TAG_DATE_TIME, dateTime);

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        new ExifRewriter().updateExifMetadataLossless(plain, out, outputSet);
        return out.toByteArray();
    }

    private static byte[] jpegWithDateTag(
            org.apache.commons.imaging.formats.tiff.taginfos.TagInfoAscii tag,
            boolean exifSubIfd,
            String rawValue
    ) throws Exception {
        byte[] plain = plainJpeg();
        TiffOutputSet outputSet = new TiffOutputSet();
        TiffOutputDirectory directory = exifSubIfd
                ? outputSet.getOrCreateExifDirectory()
                : outputSet.getOrCreateRootDirectory();
        directory.add(tag, rawValue);

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        new ExifRewriter().updateExifMetadataLossless(plain, out, outputSet);
        return out.toByteArray();
    }

    private static BufferedImage blankImage() {
        BufferedImage image = new BufferedImage(50, 50, BufferedImage.TYPE_INT_RGB);
        for (int x = 0; x < 50; x++) {
            for (int y = 0; y < 50; y++) {
                image.setRGB(x, y, 0x6496C8);
            }
        }
        return image;
    }

    private static byte[] encode(BufferedImage image) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ImageIO.write(image, "jpg", out);
        return out.toByteArray();
    }
}
