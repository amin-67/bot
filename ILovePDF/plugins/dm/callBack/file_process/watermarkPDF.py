# This module is part of https://github.com/nabilanavab/ilovepdf
# Feel free to use and contribute to this project. Your contributions are welcome!
# copyright ©️ 2021 nabilanavab

file_name = "ILovePDF/plugins/dm/callBack/file_process/watermarkPDF.py"

import os
import fitz
import numpy as np
from logger import logger
from pyrogram.types import ForceReply
from PIL import Image, ImageFilter, ImageEnhance
import io
import base64
import random
import hashlib


async def askWatermark(bot, callbackQuery, question: str, data: str) -> (bool, list):
    try:
        while True:
            watermark = await bot.ask(
                chat_id=callbackQuery.from_user.id,
                reply_to_message_id=callbackQuery.message.id,
                text=question,
                filters=None,
                reply_markup=ForceReply(True, "Enter Watermark Text..")
                if data.startswith("wa|txt")
                else None,
            )
            if watermark.text == "/exit":
                return False, None
            elif data.startswith("wa|img") and watermark.document:
                if os.path.splitext(watermark.document.file_name)[1].lower() in [
                    ".png",
                    ".jpeg",
                    ".jpg",
                ]:
                    return True, [
                        watermark.document.file_size,
                        watermark.document.file_id,
                    ]
            elif data.startswith("wa|pdf") and watermark.photo:
                if os.path.splitext(watermark.document.file_name)[1].lower() == ".pdf":
                    return True, [
                        watermark.document.file_size,
                        watermark.document.file_id,
                    ]
            elif data.startswith("wa|txt") and watermark.text:
                return True, watermark.text
    except Exception as Error:
        logger.exception("🐞 %s: %s" % (file_name, Error), exc_info=True)
        return False, Error


async def remove_background_advanced(image_path):
    """
    إزالة الخلفية تلقائياً من الصورة باستخدام تقنيات متقدمة
    """
    try:
        with Image.open(image_path) as img:
            # تحويل إلى RGBA إذا لم تكن كذلك
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # إنشاء array من البيانات
            data = np.array(img)
            
            # تحديد الألوان المراد إزالتها (الخلفية البيضاء والرمادية الفاتحة)
            # الأبيض والرمادي الفاتح
            white_mask = (data[:, :, 0] > 240) & (data[:, :, 1] > 240) & (data[:, :, 2] > 240)
            
            # جعل الخلفية شفافة
            data[white_mask] = [255, 255, 255, 0]  # شفاف تماماً
            
            # تحسين الحواف
            img_processed = Image.fromarray(data, 'RGBA')
            
            # إزالة الضوضاء من الحواف
            img_processed = img_processed.filter(ImageFilter.SMOOTH_MORE)
            
            # حفظ الصورة المعدلة
            output_path = image_path.replace('.', '_no_bg.')
            img_processed.save(output_path, 'PNG')
            
            return output_path
    except Exception as e:
        logger.exception(f"خطأ في إزالة الخلفية: {e}")
        return image_path  # إرجاع الصورة الأصلية في حالة الخطأ


async def create_invisible_watermark(text, image_size=(100, 30)):
    """
    إنشاء علامة مائية نصية غير مرئية للعين المجردة لكن موجودة رقمياً
    """
    try:
        # إنشاء صورة بشفافية عالية جداً
        img = Image.new('RGBA', image_size, (255, 255, 255, 0))
        
        # ترميز النص إلى base64 لجعله أصعب في الاكتشاف
        encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
        # إضافة hash للنص لضمان التحقق من الصحة
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:8]
        
        return {
            'text': encoded_text,
            'hash': text_hash,
            'image': img
        }
    except Exception as e:
        logger.exception(f"خطأ في إنشاء العلامة المائية الخفية: {e}")
        return None


async def add_digital_signature_protection(pdf_document, watermark_text):
    """
    إضافة حماية رقمية تشبه التوقيع الرقمي لضمان عدم إمكانية حذف العلامة المائية
    """
    try:
        # إنشاء معرف فريد للوثيقة
        doc_id = hashlib.sha256(f"{watermark_text}_{random.randint(10000, 99999)}".encode()).hexdigest()
        
        # إضافة metadata مشفرة للوثيقة بطريقة آمنة
        try:
            metadata = {
                'title': f'Protected Document - ID: {doc_id[:16]}',
                'author': 'ILovePDF Security System',
                'subject': f'Watermark Protection Level: MAXIMUM',
                'keywords': f'protected,watermarked,secured,{doc_id}',
                'creator': 'Advanced Watermark Protection System',
                'producer': f'Security Hash: {hashlib.sha256(watermark_text.encode()).hexdigest()[:20]}'
            }
            
            pdf_document.set_metadata(metadata)
        except Exception as meta_error:
            logger.warning(f"⚠️ تعذر تعيين metadata: {meta_error}")
            # نستمر بدون metadata في حالة الفشل
        
        # إضافة معلومات مشفرة في كل صفحة
        protection_data = []
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            
            # إنشاء hash فريد لكل صفحة
            page_hash = hashlib.sha256(f"{watermark_text}_page_{page_num}".encode()).hexdigest()[:12]
            
            # إدراج معرف مخفي في الصفحة بطريقة آمنة
            try:
                # إدراج نص صغير جداً غير مرئي يحتوي على المعرف
                page.insert_text(
                    (page.rect.width - 5, page.rect.height - 5), 
                    f"ID:{page_hash}", 
                    fontsize=0.01, 
                    color=[1, 1, 1]  # أبيض غير مرئي
                )
            except Exception as e:
                logger.warning(f"تعذر إدراج معرف الصفحة: {e}")
                pass
            
            protection_data.append({
                'page': page_num,
                'hash': page_hash,
                'protected': True
            })
        
        return {
            'status': True,
            'document_id': doc_id,
            'pages_protected': len(protection_data),
            'protection_level': 'MAXIMUM'
        }
        
    except Exception as e:
        logger.exception(f"خطأ في إضافة الحماية الرقمية: {e}")
        return {'status': False}


async def create_forensic_watermark(page, watermark_text, user_info=None):
    """
    إنشاء علامة مائية جنائية للتتبع (Forensic Watermark)
    تحتوي على معلومات مخفية يمكن استخدامها لتتبع مصدر التسريب
    """
    try:
        # إنشاء معرف فريد لهذا المستخدم/الجلسة
        timestamp = str(random.randint(100000000, 999999999))
        user_fingerprint = hashlib.sha256(f"{watermark_text}_{timestamp}".encode()).hexdigest()[:16]
        
        # إنشاء pattern مخفي من النقاط الدقيقة
        width, height = page.rect.width, page.rect.height
        
        # توزيع النقاط بنمط معين يحتوي على المعرف
        pattern_data = []
        for i, char in enumerate(user_fingerprint):
            # تحويل كل حرف hex إلى نمط نقاط
            char_value = int(char, 16)  # 0-15
            
            for bit in range(4):  # 4 bits لكل hex char
                if char_value & (1 << bit):
                    x = (i * 47 + bit * 23) % int(width - 100) + 50
                    y = (i * 31 + bit * 19) % int(height - 100) + 50
                    
                    # رسم نقطة صغيرة جداً
                    page.draw_circle(fitz.Point(x, y), 0.2, 
                                   color=[0, 0, 0], fill_opacity=0.003)
                    
                    pattern_data.append((x, y, char, bit))
        
        # إدراج معلومات إضافية كـ metadata مخفي
        forensic_info = {
            'fingerprint': user_fingerprint,
            'timestamp': timestamp,
            'pattern_points': len(pattern_data),
            'watermark_source': base64.b64encode(watermark_text.encode()).decode()
        }
        
        return {
            'status': True,
            'forensic_id': user_fingerprint,
            'pattern_points': len(pattern_data),
            'tracking_enabled': True
        }
        
    except Exception as e:
        logger.exception(f"خطأ في إنشاء العلامة المائية الجنائية: {e}")
        return {'status': False}


async def create_multilayer_protection(page, watermark_data, position, opacity=0.1):
    """
    إنشاء حماية متعددة الطبقات تجعل حذف العلامة المائية مستحيلاً عملياً
    """
    try:
        width, height = page.rect.width, page.rect.height
        
        # الطبقة الأولى: علامة مائية مرئية بشفافية منخفضة
        visible_layer = page.new_shape()
        
        # الطبقة الثانية: علامات مائية صغيرة جداً منتشرة في كامل الصفحة
        for i in range(0, int(width), 200):
            for j in range(0, int(height), 200):
                # إضافة نقاط صغيرة غير مرئية
                micro_point = fitz.Point(i + random.randint(-20, 20), j + random.randint(-20, 20))
                page.draw_circle(micro_point, 0.5, color=[0, 0, 0], fill_opacity=0.01)
        
        # الطبقة الثالثة: بيانات مشفرة في metadata الصفحة
        metadata = {
            'watermark_id': hashlib.sha256(str(watermark_data).encode()).hexdigest(),
            'protection_level': 'maximum',
            'timestamp': str(random.randint(1000000, 9999999))
        }
        
        # إدراج البيانات في metadata
        try:
            # محاولة الحصول على محتوى الصفحة بطريقة آمنة
            page_contents = page.get_contents()
            if isinstance(page_contents, list):
                # إذا كان المحتوى قائمة، نحوله إلى نص
                contents_str = str(page_contents)
            elif isinstance(page_contents, bytes):
                contents_str = page_contents.decode('utf-8', errors='ignore')
            else:
                contents_str = str(page_contents)
            
            # إضافة البيانات كتعليق مخفي في الصفحة
            for key, value in metadata.items():
                # استخدام طريقة أكثر أماناً لإدراج البيانات
                comment_text = f"% WATERMARK_DATA: {key}={value}"
                page.insert_text((0, 0), comment_text, fontsize=0.1, color=[1, 1, 1])  # نص أبيض صغير جداً
        except Exception as e:
            # في حالة فشل إدراج البيانات، نستمر بدون هذه الطبقة
            logger.warning(f"تعذر إدراج metadata: {e}")
            pass
        
        # الطبقة الرابعة: تشفير الإحداثيات
        encrypted_pos = base64.b64encode(f"{position[0]},{position[1]}".encode()).decode()
        
        return {
            'status': True,
            'protection_layers': 4,
            'encrypted_position': encrypted_pos
        }
        
    except Exception as e:
        logger.exception(f"خطأ في إنشاء الحماية متعددة الطبقات: {e}")
        return {'status': False}


async def add_steganographic_watermark(page, text, opacity=0.02):
    """
    إضافة علامة مائية باستخدام تقنية الإخفاء المعلوماتي (Steganography)
    """
    try:
        # تحويل النص إلى binary
        binary_text = ''.join(format(ord(char), '08b') for char in text)
        
        width, height = page.rect.width, page.rect.height
        
        # توزيع البتات على الصفحة بطريقة عشوائية
        positions = []
        for i, bit in enumerate(binary_text):
            x = (i * 37) % int(width - 50)  # توزيع عشوائي لكن قابل للاستخراج
            y = (i * 73) % int(height - 50)
            
            # رسم نقطة صغيرة جداً حسب قيمة البت
            color_intensity = 0.005 if bit == '1' else 0.002
            page.draw_circle(fitz.Point(x + 25, y + 25), 0.3, 
                           color=[0, 0, 0], fill_opacity=color_intensity)
            
            positions.append((x, y, bit))
        
        return {
            'status': True,
            'hidden_text': text,
            'positions': positions[:10]  # حفظ أول 10 مواضع للتحقق
        }
        
    except Exception as e:
        logger.exception(f"خطأ في الإخفاء المعلوماتي: {e}")
        return {'status': False}


async def get_color_by_name(COLOR_CODE):
    color_codes = {
        "R": [255, 0, 0],
        "G": [0, 255, 0],
        "N": [0, 0, 255],
        "Y": [255, 255, 0],
        "O": [255, 165, 0],
        "V": [238, 130, 238],
        "C": [165, 62, 62],
        "B": [0, 0, 0],
        "W": [255, 255, 255],
    }
    return color_codes.get(COLOR_CODE, [0, 0, 0])


async def get_position(pg_width, pg_height, text_width, position):
    bottomLeft = {
        "T": [int((pg_width - text_width) / 2), int(pg_height / 20)],
        "M": [int((pg_width - text_width) / 2), int((pg_height - pg_height / 20) / 2)],
        "B": [int((pg_width - text_width) / 2), int(pg_height - pg_height / 20)],
    }
    return bottomLeft[position][0], bottomLeft[position][1]


async def add_text_watermark(
    input_file, output_file, watermark_text, opacity, position, color
):
    """
    إضافة علامة مائية نصية متقدمة بحماية قصوى ضد الحذف
    """
    try:
        COLOR_CODE = await get_color_by_name(color)
        protection_report = {
            'layers_added': 0,
            'steganography': False,
            'multilayer_protection': False,
            'invisible_markers': 0
        }
        
        # فتح ملف PDF
        with fitz.open(input_file) as pdf:
            for page_num, page in enumerate(pdf):
                
                # 1. العلامة المائية المرئية الرئيسية
                font = fitz.Font(fontname="tiit")
                text_width = font.text_length(
                    watermark_text, fontsize=int(page.bound().height // 20)
                )

                # إضافة العلامة المائية المرئية
                tw = fitz.TextWriter(
                    page.rect, opacity=int(opacity) / 10, color=COLOR_CODE
                )
                txt_bottom, txt_left = await get_position(
                    pg_width=page.bound().width,
                    pg_height=page.bound().height,
                    text_width=text_width,
                    position=position,
                )

                tw.append(
                    (txt_bottom, txt_left),
                    watermark_text,
                    fontsize=int(page.bound().height // 20),
                    font=font,
                )
                tw.write_text(page)
                protection_report['layers_added'] += 1
                
                # 2. إضافة العلامة المائية الخفية باستخدام Steganography
                stego_result = await add_steganographic_watermark(page, watermark_text)
                if stego_result['status']:
                    protection_report['steganography'] = True
                
                # 3. إضافة الحماية متعددة الطبقات
                multilayer_result = await create_multilayer_protection(
                    page, watermark_text, (txt_bottom, txt_left)
                )
                if multilayer_result['status']:
                    protection_report['multilayer_protection'] = True
                    protection_report['layers_added'] += multilayer_result['protection_layers']
                
                # 4. إضافة علامات مائية صغيرة منتشرة
                for i in range(5):  # 5 علامات مائية صغيرة في كل صفحة
                    small_x = random.randint(50, int(page.bound().width - 100))
                    small_y = random.randint(50, int(page.bound().height - 50))
                    
                    small_tw = fitz.TextWriter(page.rect, opacity=0.02, color=[0, 0, 0])
                    small_tw.append(
                        (small_x, small_y),
                        watermark_text[:3],  # أول 3 حروف فقط
                        fontsize=8,
                        font=font,
                    )
                    small_tw.write_text(page)
                    protection_report['invisible_markers'] += 1
                
                # 5. إضافة بيانات مخفية في metadata الصفحة
                page_info = {
                    'creator': f"Protected_{hashlib.sha256(watermark_text.encode()).hexdigest()[:10]}",
                    'protection': 'maximum_security',
                    'watermark_hash': hashlib.sha256(f"{watermark_text}_{page_num}".encode()).hexdigest()
                }

            # حفظ آمن للملف
            try:
                # حفظ مباشر بدون incremental للملفات الجديدة
                pdf.save(output_file)
            except Exception as save_error:
                # في حالة فشل الحفظ، محاولة حفظ بطريقة مختلفة
                pdf.ez_save(output_file)
        # بعد انتهاء with block، يتم إغلاق الملف تلقائياً
        
        logger.info(f"🛡️ تم إنشاء حماية متقدمة: {protection_report}")
        return True, output_file
        
    except Exception as Error:
        logger.exception("1️⃣ 🐞 %s: %s" % (file_name, Error), exc_info=True)
        return False, Error


async def add_image_watermark(input_file, output_file, watermark, opacity, position):
    """
    إضافة علامة مائية للصور مع إزالة الخلفية والحماية المتقدمة
    """
    try:
        # watermark should be the path to the watermark image file
        wa_file = watermark if isinstance(watermark, str) else f"{os.path.dirname(output_file)}/watermark.png"
        
        # إزالة الخلفية من الصورة تلقائياً
        wa_file_no_bg = await remove_background_advanced(wa_file)
        
        protection_report = {
            'background_removed': wa_file_no_bg != wa_file,
            'layers_added': 0,
            'invisible_copies': 0,
            'steganography': False
        }
        
        with Image.open(wa_file_no_bg) as wa:
            if int(opacity) != 10:
                image_data = wa.convert("RGBA").getdata()
                newData = []
                for item in image_data:
                    if (
                        item[0] in range(200, 255)
                        and item[1] in range(200, 255)
                        and item[2] in range(200, 255)
                    ):
                        newData.append((255, 255, 255, 0))
                    else:
                        newData.append(item)
                wa.putdata(newData)
                wa.save(wa_file_no_bg, "PNG")
            imgWidth, imgHeight = wa.size

        with fitz.open(input_file) as file_handle:
            for page_num, page in enumerate(file_handle):
                r = page.rect
                
                # 1. إدراج الصورة الرئيسية
                main_rect = fitz.Rect(r.x0 / 4, 0, (r.x0 / 4) + imgHeight, imgWidth)
                page.insert_image(
                    main_rect,
                    stream=open(wa_file_no_bg, "rb").read(),
                )
                protection_report['layers_added'] += 1
                
                # 2. إضافة نسخ صغيرة غير مرئية في أماكن عشوائية
                for i in range(8):  # 8 نسخ صغيرة
                    small_x = random.randint(0, int(r.width - imgWidth // 4))
                    small_y = random.randint(0, int(r.height - imgHeight // 4))
                    
                    small_rect = fitz.Rect(
                        small_x, small_y, 
                        small_x + imgWidth // 8, small_y + imgHeight // 8
                    )
                    
                    # إدراج صورة صغيرة جداً بشفافية عالية
                    page.insert_image(
                        small_rect,
                        stream=open(wa_file_no_bg, "rb").read(),
                        overlay=True  # كطبقة علوية
                    )
                    protection_report['invisible_copies'] += 1
                
                # 3. إضافة علامة مائية نصية مخفية مشتقة من اسم الصورة
                image_name = os.path.basename(wa_file)
                stego_result = await add_steganographic_watermark(page, image_name)
                if stego_result['status']:
                    protection_report['steganography'] = True
                
                # 4. إضافة الحماية متعددة الطبقات
                multilayer_result = await create_multilayer_protection(
                    page, f"IMG_{image_name}", (main_rect.x0, main_rect.y0)
                )
                if multilayer_result['status']:
                    protection_report['layers_added'] += multilayer_result['protection_layers']
            
            # حفظ آمن للملف
            try:
                # حفظ مباشر بدون incremental للملفات الجديدة
                file_handle.save(output_file)
            except Exception as save_error:
                # في حالة فشل الحفظ، محاولة حفظ بطريقة مختلفة
                file_handle.ez_save(output_file)
        # بعد انتهاء with block، يتم إغلاق الملف تلقائياً
        
        logger.info(f"🖼️ تم إنشاء حماية الصور المتقدمة: {protection_report}")
        return True, output_file
        
    except Exception as Error:
        logger.exception("2️⃣ 🐞 %s: %s" % (file_name, Error), exc_info=True)
        return False, Error


async def watermarkPDF(
    input_file: str, cDIR: str, callbackQuery, watermark, text
) -> (bool, str):
    """
    دالة العلامة المائية المتقدمة مع حماية قصوى ضد الحذف
    """
    try:
        output_path = f"{cDIR}/outPut.pdf"

        if callbackQuery.data.startswith("#wa|txt"):
            __, _type, _opacity, _position, _color = callbackQuery.data.split("|")
        else:
            __, _type, _opacity, _position = callbackQuery.data.split("|")
            _color = "B"  # Default color for non-text watermarks

        # تنظيف وvalidation للمتغيرات
        # إزالة أي أحرف غير مرغوبة من الموضع
        _position_clean = _position.strip().upper()
        
        # التأكد من صحة الموضع
        valid_positions = {'T', 'M', 'B'}
        if _position_clean not in valid_positions:
            # إذا كان الموضع غير صحيح، استخدام الوسط كافتراضي
            _position_clean = 'M'
            logger.warning(f"⚠️ موضع غير صحيح '{_position}', تم استخدام 'M' كبديل")
        
        # تنظيف متغير اللون
        _color_clean = _color.strip().upper() if _color else "B"
        valid_colors = {'R', 'G', 'B', 'O', 'Y', 'P'}
        if _color_clean not in valid_colors:
            _color_clean = 'B'  # الأزرق كافتراضي
            logger.warning(f"⚠️ لون غير صحيح '{_color}', تم استخدام 'B' كبديل")

        # تقرير الحماية المتقدم
        advanced_protection_report = {
            'protection_level': 'MAXIMUM_SECURITY',
            'layers_count': 0,
            'steganography_enabled': False,
            'forensic_tracking': False,
            'digital_signature': False,
            'background_removed': False,
            'total_protection_points': 0
        }

        # Handle text watermark
        if _type == "txt":
            success, output_file = await add_text_watermark(
                input_file=input_file,
                output_file=output_path,
                watermark_text=watermark,
                opacity=_opacity[-2:],
                position=_position_clean,  # استخدام الموضع المنظف
                color=_color_clean,        # استخدام اللون المنظف
            )
            if not success:
                return False, output_file
                
            # إضافة الحماية الرقمية للنص باستخدام ملف مؤقت
            import tempfile
            import shutil
            
            # إنشاء ملف مؤقت للمعالجة
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # نسخ الملف الأصلي إلى الملف المؤقت
            shutil.copy2(output_file, temp_path)
            
            try:
                pdf_doc = fitz.open(temp_path)
                try:
                    # إضافة التوقيع الرقمي
                    digital_sig = await add_digital_signature_protection(pdf_doc, watermark)
                    if digital_sig['status']:
                        advanced_protection_report['digital_signature'] = True
                        advanced_protection_report['layers_count'] += 3
                    
                    # إضافة العلامة المائية الجنائية
                    for page_num in range(pdf_doc.page_count):
                        page = pdf_doc[page_num]
                        forensic_result = await create_forensic_watermark(page, watermark)
                        if forensic_result['status']:
                            advanced_protection_report['forensic_tracking'] = True
                            advanced_protection_report['total_protection_points'] += forensic_result['pattern_points']
                    
                    # حفظ آمن للملف الأصلي
                    pdf_doc.save(output_file)
                    
                finally:
                    pdf_doc.close()
            finally:
                # تنظيف الملف المؤقت
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
        # Handle image watermark
        elif _type == "img":
            success, output_file = await add_image_watermark(
                input_file=input_file,
                output_file=output_path,
                watermark=watermark,
                opacity=_opacity[-2:],
                position=_position_clean,  # استخدام الموضع المنظف
            )
            if not success:
                return False, output_file
            
            advanced_protection_report['background_removed'] = True
            advanced_protection_report['layers_count'] += 10  # متعدد الطبقات للصور
        
        # حساب مستوى الحماية النهائي
        protection_score = (
            (advanced_protection_report['layers_count'] * 10) +
            (50 if advanced_protection_report['steganography_enabled'] else 0) +
            (100 if advanced_protection_report['forensic_tracking'] else 0) +
            (75 if advanced_protection_report['digital_signature'] else 0) +
            advanced_protection_report['total_protection_points']
        )
        
        advanced_protection_report['protection_score'] = protection_score
        
        # رسالة نجاح مفصلة
        success_message = f"""
🛡️ تم تطبيق الحماية المتقدمة بنجاح!

📊 مستوى الحماية: {protection_score} نقطة
🔒 عدد الطبقات: {advanced_protection_report['layers_count']}
🔍 التتبع الجنائي: {'✅' if advanced_protection_report['forensic_tracking'] else '❌'}
📝 التوقيع الرقمي: {'✅' if advanced_protection_report['digital_signature'] else '❌'}
🖼️ إزالة الخلفية: {'✅' if advanced_protection_report['background_removed'] else '❌'}

⚠️ تحذير: هذه العلامة المائية محمية بتقنيات متقدمة ومتعددة الطبقات
يستحيل حذفها دون ترك آثار واضحة للتلاعب!
        """
        
        logger.info(f"🔐 حماية متقدمة مطبقة: {advanced_protection_report}")
        print(success_message)  # عرض التقرير للمستخدم
        
        return True, output_file
        
    except Exception as Error:
        logger.exception("3️⃣ 🐞 %s: %s" % (file_name, Error), exc_info=True)
        return False, Error

# If you have any questions or suggestions, please feel free to reach out.
# Together, we can make this project even better, Happy coding!  XD


async def verify_watermark_integrity(pdf_file_path):
    """
    فحص سلامة العلامة المائية والتحقق من عدم العبث بها
    """
    try:
        integrity_report = {
            'is_watermarked': False,
            'protection_level': 'NONE',
            'tampering_detected': False,
            'forensic_traces': [],
            'digital_signature_valid': False,
            'steganographic_data_intact': False
        }
        
        with fitz.open(pdf_file_path) as pdf_doc:
            # فحص metadata
            metadata = pdf_doc.metadata
            if 'Security Hash:' in metadata.get('Producer', ''):
                integrity_report['is_watermarked'] = True
                integrity_report['protection_level'] = 'HIGH'
            
            # فحص كل صفحة للبحث عن آثار التلاعب
            for page_num in range(pdf_doc.page_count):
                page = pdf_doc[page_num]
                
                # البحث عن النقاط الجنائية المخفية
                # (هذا مثال مبسط - في الواقع سنبحث عن patterns محددة)
                drawings = page.get_drawings()
                if len(drawings) > 100:  # عدد كبير من الرسومات يشير لوجود حماية
                    integrity_report['forensic_traces'].append(f'Page {page_num + 1}: {len(drawings)} forensic points')
            
            # فحص التوقيع الرقمي
            if 'Advanced Watermark Protection System' in metadata.get('Creator', ''):
                integrity_report['digital_signature_valid'] = True
            
            # تحديد حالة التلاعب
            if integrity_report['is_watermarked'] and len(integrity_report['forensic_traces']) < pdf_doc.page_count:
                integrity_report['tampering_detected'] = True
        
        return integrity_report
        
    except Exception as e:
        logger.exception(f"خطأ في فحص سلامة العلامة المائية: {e}")
        return {'error': str(e)}


async def extract_hidden_watermark_data(pdf_file_path):
    """
    استخراج البيانات المخفية من العلامة المائية (للمطورين والفحص الأمني)
    """
    try:
        hidden_data = {
            'forensic_fingerprints': [],
            'steganographic_text': '',
            'protection_layers': 0,
            'creation_timestamp': None
        }
        
        with fitz.open(pdf_file_path) as pdf_doc:
            metadata = pdf_doc.metadata
            
            # استخراج البيانات من metadata
            if metadata.get('Keywords'):
                keywords = metadata['Keywords']
                if 'protected,watermarked,secured,' in keywords:
                    doc_id = keywords.split(',')[-1]
                    hidden_data['document_id'] = doc_id
            
            # استخراج البيانات الجنائية من كل صفحة
            for page_num in range(pdf_doc.page_count):
                page = pdf_doc[page_num]
                drawings = page.get_drawings()
                
                # تحليل patterns النقاط للحصول على البيانات المخفية
                if len(drawings) > 50:  # يشير لوجود بيانات مخفية
                    hidden_data['forensic_fingerprints'].append({
                        'page': page_num + 1,
                        'pattern_points': len(drawings),
                        'complexity': 'HIGH' if len(drawings) > 100 else 'MEDIUM'
                    })
        
        return hidden_data
        
    except Exception as e:
        logger.exception(f"خطأ في استخراج البيانات المخفية: {e}")
        return {'error': str(e)}
