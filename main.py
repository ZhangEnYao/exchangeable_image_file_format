import functools
import pathlib
import dataclasses
import math
import enum
import os, pathlib

from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS, IFD
import tqdm

GOLDEN_RATIO = (math.sqrt(5)-1)/2

class Extensions(enum.Enum):
    JPG = '.jpg'
    JPEG = '.jpeg'

class Information:

    DELIMITER = '  '

    def __new__(cls, *informations):
        return cls.DELIMITER.join(informations)

class ImageFileFormat:

    def __new__(cls, image_file_format):
        return str(image_file_format).strip()

@dataclasses.dataclass
class Source:

    fonts = ('source', 'fonts')
    resources = ('source', 'resources')
    productions = ('source', 'productions')

    def __new__(cls, *sources):
        return os.path.join(*sources)

@dataclasses.dataclass
class Configurations:

    EXTENSION = 'jpg'
    FONT = 'Fuji-Regular.otf'


class ExchangeableImageFileFormat:

    def __init__(self, file: str):

        self.file = pathlib.Path(file)
    
    @functools.cached_property
    def image(self):

        return Image.open(self.file)

    @functools.cached_property
    def exchangeable_image_file_formats(self):

        exif = self.image.getexif()

        exchangeable_image_file_format = {
            TAGS.get(key, key): value
            for key, value in (*exif.items(), *exif.get_ifd(IFD.Exif).items())
        }

        return exchangeable_image_file_format
    
    @functools.cached_property
    def camera(self):

        camera = '{make} {model}'.format(
            make=ImageFileFormat(self.exchangeable_image_file_formats['Make']),
            model=ImageFileFormat(self.exchangeable_image_file_formats['Model']),
        )

        return camera

    @functools.cached_property
    def lens(self):

        lens = '{lens_make} {lens_model}'.format(
            lens_make=ImageFileFormat(self.exchangeable_image_file_formats.get('LensMake', '')),
            lens_model=ImageFileFormat(self.exchangeable_image_file_formats.get('LensModel', '')),
        )

        return lens

    @functools.cached_property
    def exposure(self):

        exposure = '{focal_length}mm f{aperture} 1/{shutter_speed}s ISO{speed_ratings} {exposure_bias_value}EV'.format(
            focal_length=ImageFileFormat(self.exchangeable_image_file_formats['FocalLength']),
            aperture=ImageFileFormat(self.exchangeable_image_file_formats['FNumber']),
            shutter_speed=ImageFileFormat(1/self.exchangeable_image_file_formats['ExposureTime']),
            speed_ratings=ImageFileFormat(self.exchangeable_image_file_formats['ISOSpeedRatings']),
            exposure_bias_value=ImageFileFormat(self.exchangeable_image_file_formats['ExposureBiasValue']),
        )
        
        return exposure
    
    @functools.cached_property
    def timestamp(self):

        timestamp = '{timestamp} {timezone}'.format(
            timestamp=ImageFileFormat(self.exchangeable_image_file_formats['DateTime']),
            timezone=ImageFileFormat(self.exchangeable_image_file_formats['OffsetTime']),
        )
        
        return timestamp
    
    def process(self):
        
        width, height = self.image.size
        
        border = max(width, height)
        margin = math.floor((math.sqrt((height*width)/GOLDEN_RATIO) - border)/2)
        frame = (border + 2*margin, border + 2*margin)

        base = Image.new(mode="RGB", size=frame, color=(255, 255, 255))
        base.paste(self.image, box=(margin, margin))
        base.resize(size=frame, resample=Image.LANCZOS)

        if width < height:
            base = base.transpose(Image.ROTATE_270)

        draw = ImageDraw.Draw(base)
        font = ImageFont.truetype(font=os.path.join(*Source.fonts, Configurations.FONT), size=math.floor((GOLDEN_RATIO*GOLDEN_RATIO*margin*72/96)))
        fill = (math.floor(256*GOLDEN_RATIO-1), math.floor(256*GOLDEN_RATIO-1), math.floor(256*GOLDEN_RATIO-1))

        draw.text(
            text=Information(self.timestamp),
            xy=(margin+border-draw.textlength(self.timestamp, font=font), margin+border),
            align="right",
            fill=fill,
            font=font,
        )
        draw.text(
            text=Information(self.camera, self.lens, self.exposure),
            xy=(margin, margin+border),
            align="left",
            fill=fill,
            font=font,
        )

        if width < height:
            base = base.transpose(Image.ROTATE_90)

        base.save(Source(*Source.productions, f'{self.file.stem}.{Configurations.EXTENSION}'))

for directory in tqdm.tqdm(os.listdir(Source(*Source.resources))):
    directory = pathlib.Path(Source(*Source.resources, directory))
    ExchangeableImageFileFormat(file=directory).process()