# SRT Check AR

أداة سطر أوامر لفحص ملفات الترجمة العربية بصيغة SRT قبل تسليم الفيديو. تعمل محليًا وتعرض رقم السطر لكل مشكلة.

## الاستخدام

شغّل الأداة من هذا المجلد باستخدام Python 3.10 أو أحدث.

```sh
python srt_check.py example.srt
python srt_check.py "مشروعي.srt" --max-chars 38 --max-lines 2 --max-cps 18
```

تفحص الأداة صيغة التوقيت وترتيبه، وتداخل المقاطع، والنص الفارغ، وعدد الأسطر، وطول السطر، وسرعة القراءة. لا يدخل التشكيل وعلامات اتجاه النص في عدّ الحروف. الحدود الافتراضية قابلة للتعديل حسب نمط الترجمة.

## English

SRT Check AR is a dependency-free command-line checker for UTF-8 SubRip files, with character counting that ignores Arabic diacritics and direction marks. It reports malformed or overlapping timings, empty cues, excessive line length or line count, and fast reading speeds. It reads the input file without modifying it.

- Exit status `0` means the checks passed.
- Exit status `1` means the checker found issues in the subtitles.
- Exit status `2` means the file could not be read or the command arguments were invalid.

## الاختبارات والمساهمة

```sh
python -B -m unittest -v
```

إذا واجهت نتيجة غير متوقعة، افتح بلاغًا في GitHub Issues. اذكر أمر التشغيل، والنتيجة التي ظهرت، والنتيجة التي توقعتها، وأرفق مثال SRT قصيرًا يمكنك مشاركته علنًا.

## أفكار للتطوير

- إضافة واجهة عربية بسحب الملف وإفلاته.
- إضافة تقرير JSON لاستخدام النتائج في أدوات المونتاج.
- جمع أمثلة مصرح بنشرها لتجربة الفحص على ترجمات تختلف في أسلوبها وترميزها.
