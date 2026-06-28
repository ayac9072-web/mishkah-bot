# -*- coding: utf-8 -*-
"""
بوت مشكاة الديني - الإصدار 3.0 (ملف واحد)
يحتوي: القرآن الكريم (114 سورة، رواية ورش)، الأذكار، الأحاديث، مواقيت الصلاة،
المسبحة (محفوظة في قاعدة بيانات)، وأسئلة دينية عشوائية.

هذا الإصدار مُدمج في ملف واحد فقط لتسهيل التشغيل على الهاتف (Pydroid)،
بدون الحاجة لإدارة عدة ملفات بايثون منفصلة بجانب بعضها.
"""

import random
import logging
import sqlite3
import threading
import requests
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ضع التوكن الخاص بك هنا
TOKEN = "8968809283:AAF7Ko7t1WELChbP8qY0ACBrZgrceAe7ToI"

# تسجيل الأخطاء في الطرفية لتسهيل تتبعها أثناء التشغيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ============================================================
# القسم 1: البيانات الثابتة (أسماء السور، الأذكار، الأحاديث، الأسئلة)
# ============================================================

# ============== أسماء السور (114 سورة) ==============
SURAH_NAMES = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف",
    "الأنفال", "التوبة", "يونس", "هود", "يوسف", "الرعد", "إبراهيم", "الحجر",
    "النحل", "الإسراء", "الكهف", "مريم", "طه", "الأنبياء", "الحج", "المؤمنون",
    "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص",
    "الزمر", "غافر", "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية",
    "الأحقاف", "محمد", "الفتح", "الحجرات", "ق", "الذاريات", "الطور", "النجم",
    "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك",
    "القلم", "الحاقة", "المعارج", "نوح", "الجن", "المزمل", "المدثر", "القيامة",
    "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس", "التكوير", "الانفطار",
    "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر",
    "البلد", "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر",
    "البينة", "الزلزلة", "العاديات", "القارعة", "التكاثر", "العصر", "الهمزة",
    "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر", "المسد",
    "الإخلاص", "الفلق", "الناس"
]

SURAHS_PER_PAGE = 8  # في الأزرار التفاعلية (Inline) نستخدم عدداً أقل لكل صفحة لتناسب الشاشة


# ============== أذكار الصباح (موسعة) ==============
MORNING_AZKAR = [
    "أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، "
    "له الملك وله الحمد، وهو على كل شيء قدير، رب أسألك خير ما في هذا اليوم "
    "وخير ما بعده، وأعوذ بك من شر ما في هذا اليوم وشر ما بعده.",

    "اللهم بك أصبحنا، وبك أمسينا، وبك نحيا، وبك نموت، وإليك المصير.",

    "اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك "
    "ما استطعت، أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي، فإنه لا يغفر الذنوب "
    "إلا أنت. (سيد الاستغفار)",

    "اللهم إني أصبحت أشهدك، وأشهد حملة عرشك، وملائكتك، وجميع خلقك، أنك أنت "
    "الله لا إله إلا أنت وحدك لا شريك لك، وأن محمداً عبدك ورسولك. (×4)",

    "اللهم ما أصبح بي من نعمة أو بأحد من خلقك فمنك وحدك، لا شريك لك، فلك "
    "الحمد ولك الشكر.",

    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري، لا إله "
    "إلا أنت. اللهم إني أعوذ بك من الكفر والفقر، وأعوذ بك من عذاب القبر، "
    "لا إله إلا أنت. (×3)",

    "حسبي الله لا إله إلا هو، عليه توكلت وهو رب العرش العظيم. (×7)",

    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء، وهو السميع "
    "العليم. (×3)",

    "رضيت بالله رباً، وبالإسلام ديناً، وبمحمد ﷺ نبياً. (×3)",

    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله، ولا تكلني إلى نفسي طرفة عين.",

    "أصبحنا على فطرة الإسلام، وعلى كلمة الإخلاص، وعلى دين نبينا محمد ﷺ، "
    "وعلى ملة أبينا إبراهيم، حنيفاً مسلماً وما كان من المشركين.",

    "سبحان الله وبحمده. (×100)",

    "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء "
    "قدير. (×10 أو ×100)",

    "أستغفر الله وأتوب إليه. (×100)",

    "اللهم صل وسلم وبارك على نبينا محمد.",

    "سبحان الله، والحمد لله، ولا إله إلا الله، والله أكبر. (×4 على الأقل)",

    "اللهم إني أسألك العافية في الدنيا والآخرة.",

    "اللهم أعني على ذكرك وشكرك وحسن عبادتك.",

    "اللهم إني أسألك علماً نافعاً، ورزقاً طيباً، وعملاً متقبلاً.",

    "اللهم إنا نعوذ بك من أن نشرك بك شيئاً نعلمه، ونستغفرك لما لا نعلمه.",
]

# ============== أذكار المساء (موسعة) ==============
EVENING_AZKAR = [
    "أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، "
    "له الملك وله الحمد، وهو على كل شيء قدير، رب أسألك خير هذه الليلة وخير "
    "ما بعدها، وأعوذ بك من شر هذه الليلة وشر ما بعدها.",

    "اللهم بك أمسينا، وبك أصبحنا، وبك نحيا، وبك نموت، وإليك المصير.",

    "اللهم أنت ربي لا إله إلا أنت، خلقتني وأنا عبدك، وأنا على عهدك ووعدك "
    "ما استطعت، أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي، فإنه لا يغفر الذنوب "
    "إلا أنت. (سيد الاستغفار)",

    "اللهم إني أمسيت أشهدك، وأشهد حملة عرشك، وملائكتك، وجميع خلقك، أنك أنت "
    "الله لا إله إلا أنت وحدك لا شريك لك، وأن محمداً عبدك ورسولك. (×4)",

    "اللهم ما أمسى بي من نعمة أو بأحد من خلقك فمنك وحدك، لا شريك لك، فلك "
    "الحمد ولك الشكر.",

    "اللهم عافني في بدني، اللهم عافني في سمعي، اللهم عافني في بصري، لا إله "
    "إلا أنت. اللهم إني أعوذ بك من الكفر والفقر، وأعوذ بك من عذاب القبر، "
    "لا إله إلا أنت. (×3)",

    "حسبي الله لا إله إلا هو، عليه توكلت وهو رب العرش العظيم. (×7)",

    "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء، وهو السميع "
    "العليم. (×3)",

    "رضيت بالله رباً، وبالإسلام ديناً، وبمحمد ﷺ نبياً. (×3)",

    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله، ولا تكلني إلى نفسي طرفة عين.",

    "أمسينا وأمسى الملك لله، نسأله خير هذه الليلة، فتح هذه الليلة، ونصرها، "
    "ونورها، وبركتها، وهداها، ونعوذ به من شر ما فيها وشر ما بعدها.",

    "سبحان الله وبحمده. (×100)",

    "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء "
    "قدير. (×10 أو ×100)",

    "أستغفر الله وأتوب إليه. (×100)",

    "اللهم صل وسلم وبارك على نبينا محمد.",

    "سبحان الله، والحمد لله، ولا إله إلا الله، والله أكبر. (×4 على الأقل)",

    "اللهم إني أسألك العافية في الدنيا والآخرة.",

    "اللهم أعني على ذكرك وشكرك وحسن عبادتك.",

    "اللهم بارك لنا في ليلنا، واحفظنا من كل سوء.",

    "اللهم إنا نعوذ بك من أن نشرك بك شيئاً نعلمه، ونستغفرك لما لا نعلمه.",
]


# ============== بنك الأحاديث الصحيحة (ثابت في الكود، بدون إنترنت) ==============
# كل حديث: النص، الراوي/المصدر المختصر، والموضوع (يُستخدم في البحث)
HADITH_BANK = [
    {
        "text": "عن أبي هريرة رضي الله عنه أن رسول الله ﷺ قال: «إنما الأعمال بالنيات، "
                "وإنما لكل امرئ ما نوى».",
        "source": "متفق عليه",
        "topic": "النية والإخلاص",
    },
    {
        "text": "عن النعمان بن بشير رضي الله عنه عن النبي ﷺ قال: «الحلال بيّن، والحرام "
                "بيّن، وبينهما أمور مشتبهات لا يعلمها كثير من الناس، فمن اتقى الشبهات "
                "فقد استبرأ لدينه وعرضه».",
        "source": "متفق عليه",
        "topic": "الحلال والحرام",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «من كان يؤمن بالله "
                "واليوم الآخر فليقل خيراً أو ليصمت».",
        "source": "متفق عليه",
        "topic": "حسن الكلام",
    },
    {
        "text": "عن أنس بن مالك رضي الله عنه قال: قال رسول الله ﷺ: «لا يؤمن أحدكم حتى "
                "يحب لأخيه ما يحب لنفسه».",
        "source": "متفق عليه",
        "topic": "الأخوة والمحبة",
    },
    {
        "text": "عن عبد الله بن عمرو رضي الله عنهما عن النبي ﷺ قال: «المسلم من سلم "
                "المسلمون من لسانه ويده».",
        "source": "رواه البخاري",
        "topic": "آداب اللسان",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «من حسن إسلام المرء "
                "تركه ما لا يعنيه».",
        "source": "رواه الترمذي",
        "topic": "حسن الإسلام",
    },
    {
        "text": "عن أبي ذر رضي الله عنه قال: قال رسول الله ﷺ: «اتق الله حيثما كنت، "
                "وأتبع السيئة الحسنة تمحها، وخالق الناس بخلق حسن».",
        "source": "رواه الترمذي",
        "topic": "حسن الخلق",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه أن رسول الله ﷺ قال: «الطُّهور شطر الإيمان، "
                "والحمد لله تملأ الميزان، وسبحان الله والحمد لله تملآن - أو تملأ - ما بين "
                "السماء والأرض».",
        "source": "رواه مسلم",
        "topic": "الطهارة والذكر",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «من نفّس عن مؤمن كربة "
                "من كرب الدنيا نفّس الله عنه كربة من كرب يوم القيامة».",
        "source": "رواه مسلم",
        "topic": "الإحسان للناس",
    },
    {
        "text": "عن ابن عمر رضي الله عنهما قال: قال رسول الله ﷺ: «المسلم أخو المسلم، "
                "لا يظلمه ولا يخذله ولا يكذبه ولا يحقره».",
        "source": "رواه الترمذي",
        "topic": "الأخوة والمحبة",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه أن رسول الله ﷺ قال: «من كان في حاجة أخيه "
                "كان الله في حاجته».",
        "source": "متفق عليه",
        "topic": "الإحسان للناس",
    },
    {
        "text": "عن عمر بن الخطاب رضي الله عنه قال: سمعت رسول الله ﷺ يقول: «إنما "
                "الأعمال بالنيات» (الحديث الكامل في النية).",
        "source": "متفق عليه",
        "topic": "النية والإخلاص",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «الكلمة الطيبة صدقة».",
        "source": "متفق عليه",
        "topic": "حسن الكلام",
    },
    {
        "text": "عن جابر بن عبد الله رضي الله عنهما عن النبي ﷺ قال: «كل معروف صدقة».",
        "source": "رواه البخاري",
        "topic": "الصدقة",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «اتقوا الظلم فإن "
                "الظلم ظلمات يوم القيامة، واتقوا الشح فإن الشح أهلك من كان قبلكم».",
        "source": "رواه مسلم",
        "topic": "الظلم والعدل",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «من صام رمضان إيماناً "
                "واحتساباً غفر له ما تقدم من ذنبه».",
        "source": "متفق عليه",
        "topic": "الصيام",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «الصلوات الخمس، "
                "والجمعة إلى الجمعة، ورمضان إلى رمضان، مكفرات ما بينهن إذا اجتُنبت "
                "الكبائر».",
        "source": "رواه مسلم",
        "topic": "الصلاة",
    },
    {
        "text": "عن عبد الله بن مسعود رضي الله عنه قال: سألت رسول الله ﷺ: أي العمل "
                "أحب إلى الله؟ قال: «الصلاة على وقتها».",
        "source": "متفق عليه",
        "topic": "الصلاة",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «الصدقة تطفئ الخطيئة "
                "كما يطفئ الماء النار».",
        "source": "رواه الترمذي",
        "topic": "الصدقة",
    },
    {
        "text": "عن أبي مسعود البدري رضي الله عنه عن النبي ﷺ قال: «من دلّ على خير "
                "فله مثل أجر فاعله».",
        "source": "رواه مسلم",
        "topic": "الدلالة على الخير",
    },
    {
        "text": "عن أنس رضي الله عنه قال: قال رسول الله ﷺ: «انصر أخاك ظالماً أو "
                "مظلوماً» - قيل: كيف أنصره ظالماً؟ قال: «تحجزه عن الظلم فذلك نصرك "
                "إياه».",
        "source": "رواه البخاري",
        "topic": "الأخوة والمحبة",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «من يُرد الله به "
                "خيراً يصب منه».",
        "source": "متفق عليه",
        "topic": "الصبر والابتلاء",
    },
    {
        "text": "عن سعد بن أبي وقاص رضي الله عنه عن النبي ﷺ قال: «عجباً للمؤمن، لا "
                "يقضي الله له قضاء إلا كان خيراً له».",
        "source": "رواه مسلم (بمعناه)",
        "topic": "الصبر والابتلاء",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «خيركم من تعلم القرآن "
                "وعلّمه».",
        "source": "رواه البخاري",
        "topic": "القرآن الكريم",
    },
    {
        "text": "عن عثمان بن عفان رضي الله عنه عن النبي ﷺ قال: «خيركم من تعلم القرآن "
                "وعلّمه».",
        "source": "رواه البخاري",
        "topic": "القرآن الكريم",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «من تعلم العلم لغير "
                "الله، أو أراد به غير الله، فليتبوأ مقعده من النار».",
        "source": "رواه الترمذي",
        "topic": "طلب العلم",
    },
    {
        "text": "عن أنس بن مالك رضي الله عنه قال: قال رسول الله ﷺ: «طلب العلم فريضة "
                "على كل مسلم».",
        "source": "رواه ابن ماجه",
        "topic": "طلب العلم",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «بر الوالدين» من "
                "أفضل الأعمال - وفي حديثه الآخر: «رضا الرب في رضا الوالد، وسخط الرب "
                "في سخط الوالد».",
        "source": "رواه الطبراني (بمعناه)",
        "topic": "بر الوالدين",
    },
    {
        "text": "عن عبد الله بن عمرو رضي الله عنهما أن رجلاً قال للنبي ﷺ: من أحق "
                "الناس بحسن الصحبة؟ قال: «أمك» - ثلاث مرات - ثم قال: «ثم أبوك».",
        "source": "متفق عليه (بمعناه)",
        "topic": "بر الوالدين",
    },
    {
        "text": "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ: «لا تحاسدوا، ولا "
                "تناجشوا، ولا تباغضوا، ولا تدابروا، وكونوا عباد الله إخواناً».",
        "source": "متفق عليه",
        "topic": "الأخوة والمحبة",
    },
]


# ============== بنك الأسئلة الدينية (سؤال وجواب) ==============
QUIZ_BANK = [
    {"q": "من هو أول الأنبياء؟", "a": "آدم عليه السلام."},
    {"q": "من هو خاتم الأنبياء والمرسلين؟", "a": "محمد ﷺ."},
    {"q": "كم عدد أركان الإسلام؟", "a": "خمسة: الشهادتان، الصلاة، الزكاة، الصيام، الحج."},
    {"q": "كم عدد أركان الإيمان؟", "a": "ستة: الإيمان بالله، وملائكته، وكتبه، ورسله، واليوم "
        "الآخر، والقدر خيره وشره."},
    {"q": "ما هي أول سورة نزلت في القرآن الكريم؟", "a": "سورة العلق (أول خمس آيات منها)."},
    {"q": "ما هي آخر سورة نزلت كاملة في القرآن؟", "a": "سورة النصر (والمائدة من آخر ما نزل أيضاً عند بعض العلماء)."},
    {"q": "ما اسم زوجة النبي ﷺ التي تزوجها بعد خديجة رضي الله عنها؟", "a": "سودة بنت زمعة."},
    {"q": "من هو الصحابي الملقب بـ 'سيف الله المسلول'؟", "a": "خالد بن الوليد رضي الله عنه."},
    {"q": "كم عدد أبواب الجنة؟", "a": "ثمانية أبواب."},
    {"q": "كم عدد أبواب النار؟", "a": "سبعة أبواب."},
    {"q": "من هو أول من جمع القرآن الكريم في عهد أبي بكر الصديق؟", "a": "زيد بن ثابت رضي الله عنه."},
    {"q": "في عهد من تم نسخ القرآن إلى عدة مصاحف وتوزيعها على الأمصار؟", "a": "في عهد عثمان بن عفان رضي الله عنه."},
    {"q": "ما هي السورة التي تسمى 'قلب القرآن'؟", "a": "سورة يس."},
    {"q": "ما أطول سورة في القرآن الكريم؟", "a": "سورة البقرة."},
    {"q": "ما أقصر سورة في القرآن الكريم؟", "a": "سورة الكوثر."},
    {"q": "كم عدد سور القرآن الكريم؟", "a": "114 سورة."},
    {"q": "كم عدد أجزاء القرآن الكريم؟", "a": "30 جزءاً."},
    {"q": "من هو الصحابي الذي يلقب بـ 'حبر الأمة' لكثرة علمه بالتفسير؟", "a": "عبد الله بن عباس رضي الله عنه."},
    {"q": "من هي أول امرأة أسلمت؟", "a": "خديجة بنت خويلد رضي الله عنها."},
    {"q": "من هو أول من أسلم من الرجال خارج أهل بيت النبي ﷺ؟", "a": "أبو بكر الصديق رضي الله عنه (من الرجال الأحرار البالغين)."},
    {"q": "ما اسم غار تنزل فيه الوحي على النبي ﷺ أول مرة؟", "a": "غار حراء."},
    {"q": "في أي سنة هجرية كانت غزوة بدر الكبرى؟", "a": "السنة الثانية للهجرة."},
    {"q": "في أي سنة هجرية كانت غزوة أحد؟", "a": "السنة الثالثة للهجرة."},
    {"q": "في أي سنة هجرية كان فتح مكة؟", "a": "السنة الثامنة للهجرة."},
    {"q": "من هو الخليفة الراشد الأول بعد وفاة النبي ﷺ؟", "a": "أبو بكر الصديق رضي الله عنه."},
    {"q": "من هو الخليفة الراشد الثاني؟", "a": "عمر بن الخطاب رضي الله عنه."},
    {"q": "من هو الخليفة الراشد الثالث؟", "a": "عثمان بن عفان رضي الله عنه."},
    {"q": "من هو الخليفة الراشد الرابع؟", "a": "علي بن أبي طالب رضي الله عنه."},
    {"q": "كم مرة ذُكر اسم 'محمد' صريحاً في القرآن الكريم؟", "a": "أربع مرات."},
    {"q": "ما هي الصلاة التي فيها ركعتان فقط من الفرائض؟", "a": "صلاة الفجر."},
    {"q": "كم عدد ركعات صلاة الظهر؟", "a": "أربع ركعات."},
    {"q": "كم عدد ركعات صلاة المغرب؟", "a": "ثلاث ركعات."},
    {"q": "ما هو الركن الذي يسمى 'عماد الدين'؟", "a": "الصلاة."},
    {"q": "في أي شهر هجري فُرض الصيام؟", "a": "شهر رمضان."},
    {"q": "كم مرة تكرر ذكر 'الجنة' بألفاظها في القرآن الكريم تقريباً؟", "a": "أكثر من 140 مرة (يختلف العدّ بحسب صيغ الكلمة)."},
    {"q": "من هو النبي الذي ابتلاه الله بالمرض الشديد وصبر حتى شفاه الله؟", "a": "أيوب عليه السلام."},
    {"q": "من هو النبي الذي ابتلعه الحوت؟", "a": "يونس عليه السلام."},
    {"q": "من هو النبي المعروف بـ 'خليل الله'؟", "a": "إبراهيم عليه السلام."},
    {"q": "من هو النبي المعروف بـ 'كليم الله'؟", "a": "موسى عليه السلام."},
    {"q": "من هو النبي الذي علّمه الله صنعة الدروع (الزرد)؟", "a": "داود عليه السلام."},
    {"q": "أي نبي كان يفهم لغة الطير والحيوان وملك ملكاً عظيماً؟", "a": "سليمان عليه السلام."},
    {"q": "ما هي أم المؤمنين التي كانت ابنة أبي بكر الصديق؟", "a": "عائشة رضي الله عنها."},
    {"q": "من هو مؤذن النبي ﷺ المشهور؟", "a": "بلال بن رباح رضي الله عنه."},
    {"q": "ما اسم المعركة التي حفر فيها المسلمون خندقاً حول المدينة؟", "a": "غزوة الخندق (الأحزاب)."},
    {"q": "في أي مدينة وُلد النبي محمد ﷺ؟", "a": "في مكة المكرمة."},
    {"q": "إلى أي مدينة هاجر النبي ﷺ؟", "a": "إلى المدينة المنورة (يثرب)."},
    {"q": "كم كانت مدة الدعوة السرية في مكة قبل الدعوة العلنية؟", "a": "ثلاث سنوات تقريباً."},
    {"q": "ما اسم ابنة النبي ﷺ التي تزوجها علي بن أبي طالب؟", "a": "فاطمة الزهراء رضي الله عنها."},
    {"q": "ما هو الشهر الذي ولد فيه النبي ﷺ؟", "a": "شهر ربيع الأول."},
    {"q": "كم كان عمر النبي ﷺ عند وفاته؟", "a": "ثلاث وستون سنة تقريباً."},
    {"q": "من هو كاتب الوحي المشهور الذي جمع القرآن في عهد أبي بكر؟", "a": "زيد بن ثابت رضي الله عنه."},
]


# ============================================================
# القسم 2: قاعدة البيانات (SQLite) - المستخدمون، المسبحة، آخر سورة
# ============================================================

DB_PATH = "mishkah_bot.db"

# قفل عام للكتابة، لأن sqlite3 الافتراضي ليس Thread-Safe بالكامل عند الكتابة
# المتزامنة من عدة Threads (مكتبة telegram قد تستخدم أكثر من Thread/Task).
_db_lock = threading.Lock()


def get_connection():
    """ينشئ اتصالاً جديداً بقاعدة البيانات. check_same_thread=False لأن
    مكتبة telegram قد تستدعي من Event Loop غير الـ Thread الذي أنشأ الاتصال."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """تهيئة الجداول عند أول تشغيل للبوت. يُستدعى مرة واحدة عند الإقلاع."""
    with _db_lock:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                city TEXT,
                last_surah INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # عداد المسبحة: عمود لكل نوع ذكر بدل صف واحد لكل ضغطة (أخف وأسرع للقراءة)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasbih_counters (
                user_id INTEGER PRIMARY KEY,
                subhanallah INTEGER DEFAULT 0,
                alhamdulillah INTEGER DEFAULT 0,
                allahuakbar INTEGER DEFAULT 0,
                la_ilaha_illallah INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        conn.commit()
        conn.close()


def upsert_user(user_id: int, username: str, first_name: str):
    """تسجيل مستخدم جديد أو تحديث بياناته الأساسية إن كان موجوداً."""
    with _db_lock:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name))
        conn.commit()
        conn.close()


def set_user_city(user_id: int, city: str):
    """حفظ مدينة المستخدم لاستخدامها في مواقيت الصلاة."""
    with _db_lock:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET city = ? WHERE user_id = ?", (city, user_id))
        conn.commit()
        conn.close()


def get_user_city(user_id: int):
    """إرجاع مدينة المستخدم المحفوظة، أو None إن لم تُحدد."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT city FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row["city"] if row and row["city"] else None


def set_last_surah(user_id: int, surah_number: int):
    """حفظ آخر سورة قرأها المستخدم."""
    with _db_lock:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET last_surah = ? WHERE user_id = ?", (surah_number, user_id))
        conn.commit()
        conn.close()


def get_last_surah(user_id: int):
    """إرجاع آخر سورة قرأها المستخدم، أو None."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT last_surah FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row["last_surah"] if row and row["last_surah"] else None


# ============== المسبحة ==============

TASBIH_COLUMN_MAP = {
    "subhanallah": "subhanallah",
    "alhamdulillah": "alhamdulillah",
    "allahuakbar": "allahuakbar",
    "la_ilaha_illallah": "la_ilaha_illallah",
}


def _ensure_tasbih_row(cur, user_id: int):
    cur.execute("""
        INSERT INTO tasbih_counters (user_id)
        VALUES (?)
        ON CONFLICT(user_id) DO NOTHING
    """, (user_id,))


def increment_tasbih(user_id: int, zikr_key: str) -> int:
    """يزيد عداد ذكر معيّن بمقدار 1 ويعيد القيمة الجديدة بعد الزيادة."""
    if zikr_key not in TASBIH_COLUMN_MAP:
        raise ValueError(f"ذكر غير معروف: {zikr_key}")
    column = TASBIH_COLUMN_MAP[zikr_key]

    with _db_lock:
        conn = get_connection()
        cur = conn.cursor()
        _ensure_tasbih_row(cur, user_id)
        cur.execute(f"UPDATE tasbih_counters SET {column} = {column} + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        cur.execute(f"SELECT {column} FROM tasbih_counters WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row[column] if row else 0


def get_tasbih_counters(user_id: int) -> dict:
    """يعيد قاموساً بكل عدادات الأذكار الأربعة للمستخدم."""
    conn = get_connection()
    cur = conn.cursor()
    _ensure_tasbih_row(cur, user_id)
    conn.commit()
    cur.execute("""
        SELECT subhanallah, alhamdulillah, allahuakbar, la_ilaha_illallah
        FROM tasbih_counters WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {key: 0 for key in TASBIH_COLUMN_MAP}


def reset_tasbih(user_id: int):
    """تصفير كل عدادات المسبحة لمستخدم معيّن."""
    with _db_lock:
        conn = get_connection()
        cur = conn.cursor()
        _ensure_tasbih_row(cur, user_id)
        cur.execute("""
            UPDATE tasbih_counters
            SET subhanallah = 0, alhamdulillah = 0, allahuakbar = 0, la_ilaha_illallah = 0
            WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        conn.close()


# ============================================================
# القسم 3: خدمات الإنترنت - جلب القرآن ومواقيت الصلاة
# ============================================================

# ---------- القرآن الكريم ----------

WARSH_API_BASE = "https://api.quranhub.com/v1"
WARSH_EDITION = "quran-warsh"

FALLBACK_API_BASE = "https://api.alquran.cloud/v1"
FALLBACK_EDITION = "quran-uthmani"

REQUEST_TIMEOUT = 10  # ثوان


def _fetch_surah_from(api_base: str, edition: str, surah_number: int):
    """يجلب سورة من مصدر معيّن. يرفع استثناء عند فشل الشبكة، أو يعيد None عند
    استجابة غير متوقعة من الخادم (مثل code != 200)."""
    url = f"{api_base}/surah/{surah_number}/{edition}"
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        return None
    return data["data"]


def get_surah_text(surah_number: int):
    """يجلب نص سورة كاملة برواية ورش، مع تراجع تلقائي لرواية حفص عند تعذّر
    الوصول. يعيد tuple: (نص_جاهز_للعرض أو None, رسالة_خطأ أو None)."""
    surah_data = None
    used_fallback = False

    try:
        surah_data = _fetch_surah_from(WARSH_API_BASE, WARSH_EDITION, surah_number)
    except requests.exceptions.RequestException:
        surah_data = None
    except Exception:
        surah_data = None

    if surah_data is None:
        try:
            surah_data = _fetch_surah_from(FALLBACK_API_BASE, FALLBACK_EDITION, surah_number)
            used_fallback = True
        except requests.exceptions.RequestException:
            return None, (
                "⚠️ تعذر الاتصال بخدمة جلب القرآن حالياً.\n"
                "تحقق من اتصال الإنترنت لديك وحاول مرة أخرى بعد قليل."
            )
        except Exception:
            return None, "⚠️ حدث خطأ غير متوقع أثناء جلب السورة. حاول مرة أخرى."

    try:
        surah_name = surah_data["name"]
        ayahs = surah_data["ayahs"]

        rawi_label = (
            "📖 (رواية حفص - تعذّر الوصول لرواية ورش)"
            if used_fallback else
            "📖 (رواية ورش عن نافع)"
        )
        lines = [f"{rawi_label}\n{surah_name}\n"]

        if surah_number not in (1, 9):
            lines.append("بسم الله الرحمن الرحيم\n")

        for ayah in ayahs:
            lines.append(f"{ayah['text']} ({ayah['numberInSurah']})")

        return "\n".join(lines), None

    except Exception:
        return None, "⚠️ حدث خطأ غير متوقع أثناء معالجة نص السورة."


def split_long_message(text: str, max_len: int = 3500):
    """تيليجرام يسمح بحد أقصى 4096 حرف لكل رسالة، فنقسم السور الطويلة."""
    if len(text) <= max_len:
        return [text]

    parts = []
    lines = text.split("\n")
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            parts.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        parts.append(current)
    return parts


# ---------- مواقيت الصلاة ----------

PRAYER_API_BASE = "https://api.aladhan.com/v1"

PRAYER_NAME_AR = {
    "Fajr": "الفجر",
    "Sunrise": "الشروق",
    "Dhuhr": "الظهر",
    "Asr": "العصر",
    "Sunset": "الغروب",
    "Maghrib": "المغرب",
    "Isha": "العشاء",
    "Imsak": "الإمساك",
    "Midnight": "منتصف الليل",
}

# الترتيب الزمني للصلوات الخمس فقط (يُستخدم لحساب "الصلاة القادمة")
PRAYER_ORDER = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]


def get_prayer_times(city: str, country: str = ""):
    """يجلب مواقيت الصلاة لمدينة معيّنة عبر AlAdhan API.
    يعيد tuple: (قاموس_التوقيتات أو None, رسالة_خطأ أو None)."""
    try:
        params = {"city": city, "country": country or "", "method": 4}
        # method=4 هو طريقة جامعة أم القرى المستخدمة في السعودية ومنطقة الخليج،
        # وهي قريبة من الحسابات المعتمدة في كثير من البلدان العربية.
        resp = requests.get(f"{PRAYER_API_BASE}/timingsByCity", params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 200:
            return None, (
                f"⚠️ تعذر العثور على مدينة بالاسم '{city}'.\n"
                "تأكد من كتابة اسم المدينة بشكل صحيح (يفضّل بالإنجليزية أو الاسم الشائع عالمياً)، "
                "وحاول مرة أخرى."
            )

        timings = data["data"]["timings"]
        return timings, None

    except requests.exceptions.RequestException:
        return None, (
            "⚠️ تعذر الاتصال بخدمة مواقيت الصلاة حالياً.\n"
            "تحقق من اتصال الإنترنت لديك وحاول مرة أخرى بعد قليل."
        )
    except Exception:
        return None, "⚠️ حدث خطأ غير متوقع أثناء جلب مواقيت الصلاة."


def get_next_prayer(timings: dict):
    """يحدد الصلاة القادمة من قاموس التوقيتات المُعاد من get_prayer_times.
    يعيد tuple: (اسم_الصلاة_بالعربية, الوقت) أو (None, None) عند الفشل."""
    try:
        now = datetime.now().time()
        today_times = []
        for prayer_key in PRAYER_ORDER:
            time_str = timings.get(prayer_key, "")
            # بعض استجابات الـ API تضيف منطقة زمنية مثل "05:12 (+03)"؛ نأخذ الجزء الأول فقط
            time_str_clean = time_str.split(" ")[0]
            prayer_time = datetime.strptime(time_str_clean, "%H:%M").time()
            today_times.append((prayer_key, prayer_time))

        for prayer_key, prayer_time in today_times:
            if prayer_time > now:
                return PRAYER_NAME_AR[prayer_key], timings[prayer_key].split(" ")[0]

        # إذا فات وقت كل الصلوات اليوم، فالقادمة هي فجر اليوم التالي
        first_key, first_time_str = PRAYER_ORDER[0], timings[PRAYER_ORDER[0]]
        return PRAYER_NAME_AR[first_key] + " (غداً)", first_time_str.split(" ")[0]

    except Exception:
        return None, None


# ============================================================
# القسم 4: منطق البوت - لوحات المفاتيح، المعالجات، نقطة الدخول
# ============================================================

AWAITING_CITY = "awaiting_city"
AWAITING_HADITH_SEARCH = "awaiting_hadith_search"
AWAITING_SURAH_SEARCH = "awaiting_surah_search"
user_session_state = {}


# ============================================================
# لوحات المفاتيح الرئيسية (Reply Keyboard) - تظهر أسفل الشاشة دائماً
# ============================================================

main_keyboard = ReplyKeyboardMarkup(
    [
        ["📖 القرآن الكريم", "📜 الأحاديث"],
        ["🤲 الأذكار", "🕌 مواقيت الصلاة"],
        ["📿 المسبحة", "❓ سؤال ديني"],
        ["ℹ️ عن البوت"]
    ],
    resize_keyboard=True
)

azkar_keyboard = ReplyKeyboardMarkup(
    [
        ["🌅 أذكار الصباح"],
        ["🌙 أذكار المساء"],
        ["🔙 القائمة الرئيسية"]
    ],
    resize_keyboard=True
)

hadith_keyboard = ReplyKeyboardMarkup(
    [
        ["📗 حديث عشوائي"],
        ["🔍 البحث عن حديث"],
        ["🔙 القائمة الرئيسية"]
    ],
    resize_keyboard=True
)

prayer_keyboard = ReplyKeyboardMarkup(
    [
        ["🕌 عرض المواقيت", "⏭️ الصلاة القادمة"],
        ["📍 تغيير المدينة"],
        ["🔙 القائمة الرئيسية"]
    ],
    resize_keyboard=True
)

tasbih_keyboard = ReplyKeyboardMarkup(
    [
        ["➕ سبحان الله", "➕ الحمد لله"],
        ["➕ الله أكبر", "➕ لا إله إلا الله"],
        ["🔄 تصفير العداد", "🔙 القائمة الرئيسية"]
    ],
    resize_keyboard=True
)

quran_section_keyboard = ReplyKeyboardMarkup(
    [
        ["📃 تصفح كل السور"],
        ["🔍 البحث باسم/رقم السورة"],
        ["🔙 القائمة الرئيسية"]
    ],
    resize_keyboard=True
)


# ============================================================
# دوال مساعدة لبناء الأزرار التفاعلية (Inline Keyboard) لتصفح السور
# ============================================================

def build_surah_inline_page(page: int) -> InlineKeyboardMarkup:
    """يبني صفحة أزرار تفاعلية لاختيار السورة، مع أزرار تنقّل بين الصفحات."""
    start = page * SURAHS_PER_PAGE
    end = min(start + SURAHS_PER_PAGE, len(SURAH_NAMES))

    rows = []
    row = []
    for i in range(start, end):
        surah_number = i + 1
        button = InlineKeyboardButton(
            f"{surah_number}. {SURAH_NAMES[i]}",
            callback_data=f"surah:{surah_number}"
        )
        row.append(button)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ السابقة", callback_data=f"surahpage:{page - 1}"))
    if end < len(SURAH_NAMES):
        nav_row.append(InlineKeyboardButton("التالية ▶️", callback_data=f"surahpage:{page + 1}"))
    if nav_row:
        rows.append(nav_row)

    return InlineKeyboardMarkup(rows)


def build_back_to_main_inline() -> InlineKeyboardMarkup:
    """زر تفاعلي وحيد للعودة للقائمة الرئيسية، يُستخدم أسفل النتائج التفاعلية."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="go_main")]
    ])


# ============================================================
# دوال مساعدة عامة
# ============================================================

def clear_session_state(user_id: int):
    user_session_state.pop(user_id, None)


async def send_surah_by_number(update: Update, surah_number: int, user_id: int):
    """يجلب نص السورة ويرسله، مع تقسيمه إن كان طويلاً، وحفظه كآخر سورة مقروءة."""
    if not (1 <= surah_number <= 114):
        await update.effective_message.reply_text("⚠️ رقم السورة يجب أن يكون بين 1 و114.")
        return

    await update.effective_message.reply_text("⏳ جاري جلب السورة...")
    surah_text, error = get_surah_text(surah_number)

    if error:
        await update.effective_message.reply_text(error)
        return

    set_last_surah(user_id, surah_number)

    for part in split_long_message(surah_text):
        await update.effective_message.reply_text(part)


def find_surah_by_query(query: str):
    """يبحث عن سورة بالاسم (مطابقة تامة أولاً، ثم جزئية) أو بالرقم.
    يعيد رقم السورة أو None."""
    query = query.strip()

    if query.isdigit():
        num = int(query)
        if 1 <= num <= 114:
            return num
        return None

    # إزالة "سورة" من بداية النص إن وُجدت لتسهيل المطابقة
    cleaned = query.replace("سورة", "").strip()
    if not cleaned:
        return None

    # المرحلة الأولى: مطابقة تامة (الأدق والأكثر أماناً، تتعامل بشكل صحيح
    # مع أسماء قصيرة جداً مثل "ق" و"ص")
    for i, name in enumerate(SURAH_NAMES):
        if cleaned == name:
            return i + 1

    # المرحلة الثانية: مطابقة جزئية، لكن نتجاهل أسماء السور القصيرة جداً
    # (3 أحرف أو أقل) في هذه المرحلة لمنع تطابقات زائفة مثل "ق" داخل "الفلق"
    for i, name in enumerate(SURAH_NAMES):
        if len(name) <= 3:
            continue
        if cleaned in name or name in cleaned:
            return i + 1

    return None


def search_hadith(query: str):
    """يبحث في بنك الأحاديث عن تطابق في نص الحديث أو موضوعه. يعيد قائمة نتائج."""
    query = query.strip().lower()
    results = []
    for hadith in HADITH_BANK:
        if query in hadith["text"].lower() or query in hadith["topic"].lower():
            results.append(hadith)
    return results


def format_hadith(hadith: dict) -> str:
    return f"📜 {hadith['text']}\n\n📌 {hadith['source']} | الموضوع: {hadith['topic']}"


# ============================================================
# معالج الأمر /start
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")
    clear_session_state(user.id)

    await update.message.reply_text(
        "🌿 السلام عليكم ورحمة الله وبركاته\n\n"
        "أهلاً بك في بوت مشكاة.\n"
        "اختر القسم الذي تريده.",
        reply_markup=main_keyboard
    )


# ============================================================
# المعالج الرئيسي للرسائل النصية (أزرار لوحة المفاتيح العادية)
# ============================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    user_id = user.id

    upsert_user(user_id, user.username or "", user.first_name or "")

    # ---------- التحقق أولاً: هل المستخدم في وضع انتظار إدخال خاص؟ ----------
    state = user_session_state.get(user_id)

    if state == AWAITING_CITY:
        clear_session_state(user_id)
        await handle_city_input(update, text, user_id)
        return

    if state == AWAITING_HADITH_SEARCH:
        clear_session_state(user_id)
        await handle_hadith_search_input(update, text)
        return

    if state == AWAITING_SURAH_SEARCH:
        clear_session_state(user_id)
        await handle_surah_search_input(update, text, user_id)
        return

    # ---------- القائمة الرئيسية ----------
    if text == "📖 القرآن الكريم":
        await update.message.reply_text(
            "📖 اختر طريقة الوصول للسورة:",
            reply_markup=quran_section_keyboard
        )

    elif text == "📜 الأحاديث":
        await update.message.reply_text(
            "📜 اختر ما تريد:",
            reply_markup=hadith_keyboard
        )

    elif text == "🤲 الأذكار":
        await update.message.reply_text(
            "اختر نوع الذكر:",
            reply_markup=azkar_keyboard
        )

    elif text == "🕌 مواقيت الصلاة":
        await update.message.reply_text(
            "🕌 قسم مواقيت الصلاة:",
            reply_markup=prayer_keyboard
        )

    elif text == "📿 المسبحة":
        await show_tasbih_counters(update, user_id)

    elif text == "❓ سؤال ديني":
        await send_random_quiz(update)

    elif text == "ℹ️ عن البوت":
        await update.message.reply_text(
            "بوت مشكاة\nالإصدار 3.0\n"
            "يحتوي على: القرآن الكريم (114 سورة، رواية ورش)، الأذكار، "
            "الأحاديث، مواقيت الصلاة، المسبحة المحفوظة، وأسئلة دينية.\n\n"
            "نص القرآن يُجلب لحظياً من خدمات خارجية مجانية."
        )

    elif text == "🔙 القائمة الرئيسية":
        clear_session_state(user_id)
        await update.message.reply_text(
            "تم الرجوع للقائمة الرئيسية.",
            reply_markup=main_keyboard
        )

    # ---------- قسم القرآن ----------
    elif text == "📃 تصفح كل السور":
        await update.message.reply_text(
            "📖 اختر السورة (114 سورة):",
            reply_markup=build_surah_inline_page(0)
        )

    elif text == "🔍 البحث باسم/رقم السورة":
        user_session_state[user_id] = AWAITING_SURAH_SEARCH
        await update.message.reply_text(
            "✍️ اكتب اسم السورة (مثل: البقرة) أو رقمها (مثل: 2):"
        )

    # ---------- قسم الأذكار ----------
    elif text == "🌅 أذكار الصباح":
        await update.message.reply_text("🌅 أذكار الصباح:")
        for zikr in MORNING_AZKAR:
            await update.message.reply_text(zikr)

    elif text == "🌙 أذكار المساء":
        await update.message.reply_text("🌙 أذكار المساء:")
        for zikr in EVENING_AZKAR:
            await update.message.reply_text(zikr)

    # ---------- قسم الأحاديث ----------
    elif text == "📗 حديث عشوائي":
        hadith = random.choice(HADITH_BANK)
        await update.message.reply_text(format_hadith(hadith))

    elif text == "🔍 البحث عن حديث":
        user_session_state[user_id] = AWAITING_HADITH_SEARCH
        await update.message.reply_text(
            "✍️ اكتب كلمة من نص الحديث أو موضوعه (مثل: الصدقة، بر الوالدين):"
        )

    # ---------- قسم مواقيت الصلاة ----------
    elif text == "🕌 عرض المواقيت":
        await show_prayer_times(update, user_id)

    elif text == "⏭️ الصلاة القادمة":
        await show_next_prayer(update, user_id)

    elif text == "📍 تغيير المدينة":
        user_session_state[user_id] = AWAITING_CITY
        await update.message.reply_text(
            "✍️ اكتب اسم مدينتك (مثلاً: القاهرة، أو Cairo):"
        )

    # ---------- قسم المسبحة ----------
    elif text in ["➕ سبحان الله", "➕ الحمد لله", "➕ الله أكبر", "➕ لا إله إلا الله"]:
        await handle_tasbih_increment(update, text, user_id)

    elif text == "🔄 تصفير العداد":
        reset_tasbih(user_id)
        await update.message.reply_text(
            "🔄 تم تصفير جميع العدادات.",
            reply_markup=tasbih_keyboard
        )

    else:
        await update.message.reply_text(
            "لم أفهم طلبك، اختر من الأزرار الموجودة 🙏"
        )


# ============================================================
# معالجات فرعية مفصّلة (تُستدعى من المعالج الرئيسي)
# ============================================================

async def handle_city_input(update: Update, city_text: str, user_id: int):
    """يُستدعى عندما يكتب المستخدم اسم مدينة بعد طلب 'تغيير المدينة'."""
    city = city_text.strip()
    if not city or len(city) > 100:
        await update.message.reply_text("⚠️ اسم المدينة غير صحيح، حاول مرة أخرى من القائمة.")
        return

    set_user_city(user_id, city)
    await update.message.reply_text(
        f"✅ تم حفظ مدينتك: {city}\nيمكنك الآن عرض المواقيت أو الصلاة القادمة.",
        reply_markup=prayer_keyboard
    )


async def handle_hadith_search_input(update: Update, query_text: str):
    """يُستدعى عند كتابة المستخدم كلمة بحث عن حديث."""
    query = query_text.strip()
    if not query:
        await update.message.reply_text("⚠️ يرجى كتابة كلمة بحث صحيحة.")
        return

    results = search_hadith(query)

    if not results:
        await update.message.reply_text(
            f"😕 لم يتم العثور على أحاديث متعلقة بـ «{query}» في البنك المحلي الحالي.\n"
            "جرب كلمة أخرى مثل: الصدقة، الصلاة، بر الوالدين، النية.",
            reply_markup=hadith_keyboard
        )
        return

    await update.message.reply_text(f"🔍 تم العثور على {len(results)} نتيجة:")
    for hadith in results[:10]:  # حد أقصى 10 نتائج لتجنب إغراق المحادثة
        await update.message.reply_text(format_hadith(hadith))


async def handle_surah_search_input(update: Update, query_text: str, user_id: int):
    """يُستدعى عند كتابة المستخدم اسم أو رقم سورة للبحث."""
    surah_number = find_surah_by_query(query_text)

    if surah_number is None:
        await update.message.reply_text(
            f"😕 لم أتعرف على سورة بالاسم أو الرقم «{query_text}».\n"
            "تأكد من كتابة الاسم بشكل صحيح (مثل: البقرة) أو رقم بين 1 و114.",
            reply_markup=quran_section_keyboard
        )
        return

    await send_surah_by_number(update, surah_number, user_id)


async def show_tasbih_counters(update: Update, user_id: int):
    counters = get_tasbih_counters(user_id)
    text = (
        "📿 المسبحة الإلكترونية (محفوظة دائماً)\n\n"
        f"سبحان الله: {counters['subhanallah']}\n"
        f"الحمد لله: {counters['alhamdulillah']}\n"
        f"الله أكبر: {counters['allahuakbar']}\n"
        f"لا إله إلا الله: {counters['la_ilaha_illallah']}\n\n"
        "اضغط على أحد الأذكار لزيادة عدّاده:"
    )
    await update.message.reply_text(text, reply_markup=tasbih_keyboard)


async def handle_tasbih_increment(update: Update, button_text: str, user_id: int):
    zikr_map = {
        "➕ سبحان الله": "subhanallah",
        "➕ الحمد لله": "alhamdulillah",
        "➕ الله أكبر": "allahuakbar",
        "➕ لا إله إلا الله": "la_ilaha_illallah",
    }
    zikr_key = zikr_map[button_text]
    zikr_name = button_text.replace("➕ ", "")

    try:
        new_count = increment_tasbih(user_id, zikr_key)
        await update.message.reply_text(
            f"📿 {zikr_name}\nالعدد: {new_count}",
            reply_markup=tasbih_keyboard
        )
    except Exception:
        logger.exception("فشل تحديث عداد المسبحة")
        await update.message.reply_text(
            "⚠️ حدث خطأ أثناء حفظ العداد، حاول مرة أخرى.",
            reply_markup=tasbih_keyboard
        )


async def send_random_quiz(update: Update):
    quiz = random.choice(QUIZ_BANK)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💡 عرض الإجابة", callback_data=f"quizans:{QUIZ_BANK.index(quiz)}")]
    ])
    await update.message.reply_text(f"❓ {quiz['q']}", reply_markup=keyboard)


async def show_prayer_times(update: Update, user_id: int):
    city = get_user_city(user_id)
    if not city:
        user_session_state[user_id] = AWAITING_CITY
        await update.effective_message.reply_text(
            "📍 لم تحدد مدينتك بعد. اكتب اسم مدينتك الآن (مثلاً: الرياض، أو Riyadh):"
        )
        return

    await update.effective_message.reply_text(f"⏳ جاري جلب مواقيت الصلاة لمدينة {city}...")
    timings, error = get_prayer_times(city)

    if error:
        await update.effective_message.reply_text(error)
        return

    text = (
        f"🕌 مواقيت الصلاة - {city}\n\n"
        f"🌅 الفجر: {timings['Fajr'].split(' ')[0]}\n"
        f"☀️ الظهر: {timings['Dhuhr'].split(' ')[0]}\n"
        f"🌇 العصر: {timings['Asr'].split(' ')[0]}\n"
        f"🌆 المغرب: {timings['Maghrib'].split(' ')[0]}\n"
        f"🌙 العشاء: {timings['Isha'].split(' ')[0]}"
    )
    await update.effective_message.reply_text(text)


async def show_next_prayer(update: Update, user_id: int):
    city = get_user_city(user_id)
    if not city:
        user_session_state[user_id] = AWAITING_CITY
        await update.effective_message.reply_text(
            "📍 لم تحدد مدينتك بعد. اكتب اسم مدينتك الآن (مثلاً: الرياض، أو Riyadh):"
        )
        return

    timings, error = get_prayer_times(city)
    if error:
        await update.effective_message.reply_text(error)
        return

    prayer_name, prayer_time = get_next_prayer(timings)
    if not prayer_name:
        await update.effective_message.reply_text("⚠️ تعذر حساب الصلاة القادمة حالياً.")
        return

    await update.effective_message.reply_text(
        f"⏭️ الصلاة القادمة في {city}:\n\n🕌 {prayer_name} في الساعة {prayer_time}"
    )


# ============================================================
# معالج الأزرار التفاعلية (Inline Keyboard Callbacks)
# ============================================================

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # يوقف مؤشر التحميل الدائري في تيليجرام

    data = query.data
    user_id = query.from_user.id

    if data.startswith("surahpage:"):
        page = int(data.split(":")[1])
        await query.edit_message_text(
            "📖 اختر السورة (114 سورة):",
            reply_markup=build_surah_inline_page(page)
        )

    elif data.startswith("surah:"):
        surah_number = int(data.split(":")[1])
        await send_surah_by_number(update, surah_number, user_id)

    elif data.startswith("quizans:"):
        idx = int(data.split(":")[1])
        if 0 <= idx < len(QUIZ_BANK):
            quiz = QUIZ_BANK[idx]
            await query.edit_message_text(f"❓ {quiz['q']}\n\n✅ الإجابة: {quiz['a']}")

    elif data == "go_main":
        await query.edit_message_text("تم الرجوع للقائمة الرئيسية. 🏠")


# ============================================================
# معالج الأخطاء العام
# ============================================================

async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """يُستدعى تلقائياً عند حدوث أي استثناء غير متوقع في أي معالج، بدل أن
    يتوقف البوت بالكامل. يسجّل الخطأ في الطرفية ويرسل رسالة ودّية للمستخدم."""
    logger.error("حدث استثناء غير متوقع:", exc_info=context.error)

    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ حدث خطأ غير متوقع، تم تسجيله وسنعمل على حله. حاول مرة أخرى."
            )
    except Exception:
        logger.exception("فشل حتى في إرسال رسالة الخطأ للمستخدم")


# ============================================================
# نقطة الدخول الرئيسية
# ============================================================

def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    print("البوت يعمل...")
    app.run_polling()


if __name__ == "__main__":
    main()
