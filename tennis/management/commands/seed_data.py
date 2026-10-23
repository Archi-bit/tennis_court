"""Добавить вымышленные данные для учебной демонстрации Tennis.

Запуск: python manage.py seed_data

Существующие записи и файлы не обновляются. Для моделей со slug используется
пространство имён demo-tennis-*. Для остальных — устойчивые естественные ключи.
ClubInfo создаётся только при отсутствии информации о клубе; занятые номера
кортов и совпадающие естественные ключи используются без изменений.

Все иллюстрации создаются локально: это не фотографии реальных тренеров или
реального клуба. Скачивание внешних материалов и сторонние лицензии не нужны.
Pillow используется при наличии; предусмотрен простой PNG через stdlib.
Изображения сохраняются напрямую через storage соответствующего ImageField,
чтобы upload_to не вынес файлы за пределы media/seed_data/.
"""

import hashlib
import io
import math
import struct
import zlib
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection, models, transaction
from django.utils import timezone

from tennis.models import Coach
from tennis.models import ClubInfo, ClubRule
from tennis.models import Court, CourtType
from tennis.models import GalleryImage, News
from tennis.models import PriceCategory, PriceItem, Service
from tennis.models import Tournament


MODELS = (
    ClubInfo, ClubRule, CourtType, Court, Coach, Service, PriceCategory,
    PriceItem, News, GalleryImage, Tournament,
)
DEMO_NOTE = (
    "Учебные демонстрационные данные: клуб, имена, события и цены вымышлены. "
    "Иллюстрации созданы программно и не изображают реальных сотрудников клуба."
)

RULES = (
    ("Бронирование игрового времени", "Забронируйте корт заранее. Приходите за 10 минут до начала, чтобы переодеться и подготовить инвентарь. Время разминки входит в бронь."),
    ("Отмена и перенос занятия", "Если планы изменились, предупредите администратора не позднее чем за 12 часов. Перенос зависит от наличия свободных кортов и согласуется отдельно."),
    ("Обувь для выбранного покрытия", "Играйте в чистой теннисной обуви, подходящей для покрытия. На крытых кортах используйте подошву, которая не оставляет следов."),
    ("Разминка и самочувствие", "Перед игрой уделите разминке не менее 10 минут. При боли, головокружении или резком ухудшении самочувствия остановитесь и обратитесь за помощью."),
    ("Уважение к соседним кортам", "Не выходите на соседний корт во время розыгрыша. Дождитесь паузы и попросите вернуть мяч. Громкие разговоры ведите вне игровой зоны."),
    ("Занятия детей", "Детские группы занимаются под руководством тренера. Родители передают ребёнка тренеру перед занятием и встречают его после окончания урока."),
    ("Уход за грунтовым кортом", "После игры разровняйте покрытие щёткой по указанию сотрудника клуба. Не используйте мокрый грунт, если корт временно закрыт."),
    ("Инвентарь и личные вещи", "Возвращайте арендованные ракетки и корзины с мячами после занятия. Проверяйте карманы чехлов и пользуйтесь шкафчиками для личных вещей."),
    ("Вода и чистота", "Приносите воду в закрывающейся бутылке. Стеклянную посуду и еду оставляйте вне корта. После занятия уберите упаковку и использованные мячи."),
    ("Фото и участие в мероприятиях", "Согласуйте съёмку с участниками тренировки. Фотографии детей публикуются только с согласия законного представителя. Участие в турнирах добровольное."),
)

COURT_TYPES = (
    ("clay", "Открытый грунтовый корт", "clay", False,
     "Красный грунт для длинных розыгрышей и отработки движения. Открытые площадки доступны в сухую погоду; после дождя требуется проверка покрытия."),
    ("hard", "Крытый корт с покрытием хард", "hard", True,
     "Ровное акриловое покрытие с предсказуемым отскоком. Крытый зал подходит для круглогодичных тренировок и учебных соревнований."),
    ("grass", "Корт с искусственной травой", "artificial_grass", False,
     "Искусственная трава с песчаной засыпкой для любительской игры. Перед выходом проверьте обувь и состояние покрытия вместе с администратором."),
)

COURT_NOTES = (
    "Рядом с зоной отдыха; удобен для индивидуального урока утром.",
    "Защитный экран вдоль задней линии помогает собирать мячи после подачи.",
    "Площадка для парной игры; скамейки расположены за боковым ограждением.",
    "Тихая сторона комплекса для отработки длинных розыгрышей.",
    "Ближе к учебной зоне; после игры требуется уход за грунтом.",
    "Крытый зал с равномерным освещением для вечерних тренировок.",
    "Рядом со стойкой инвентаря; подходит для работы с корзиной мячей.",
    "Место для видеоразбора техники за пределами игровой зоны.",
    "Учебная площадка для матчей начинающих с судьёй у сетки.",
    "Предусмотрена зона ожидания для следующей тренировочной группы.",
    "Открытая площадка с зелёным покрытием для любительской игры.",
    "Удобный выход к прогулочной дорожке и питьевой воде.",
    "Подходит для спокойной парной тренировки в дневные часы.",
    "Площадка рядом с местом сбора участников клубных встреч.",
    "В демонстрационном расписании закрыт на плановое обслуживание.",
)

COACHES = (
    ("Алексей Миронов", 14, "Техника ударов и подготовка любителей", "Помогает взрослым освоить надёжный удар справа, слева и первую подачу. Строит урок вокруг понятной задачи и коротких игровых упражнений."),
    ("Екатерина Соколова", 11, "Детский теннис, красный и оранжевый мяч", "Знакомит детей с теннисом через подвижные игры. Уделяет внимание координации, правилам поведения на корте и уверенности ребёнка."),
    ("Тимур Асанов", 9, "Парная игра и тактика у сетки", "Объясняет взаимодействие в паре, выбор позиции и перехваты. Использует учебные розыгрыши с постепенным увеличением темпа."),
    ("Мария Белова", 8, "Начинающие взрослые", "Подбирает упражнения для тех, кто впервые взял ракетку. Помогает освоить счёт, перемещения и стабильный обмен мячами без спешки."),
    ("Данияр Осмонов", 12, "Турнирная подготовка подростков", "Работает над принятием решений в матче и подготовкой к любительским стартам. Разбирает игровые эпизоды и ведёт дневник тренировочных целей."),
    ("Анна Воронцова", 10, "Подача и приём", "Разбивает сложные движения на небольшие этапы. На занятиях сочетает координационные задания, упражнения на точность и учебные геймы."),
    ("Сергей Лебедев", 16, "Игра на грунте и работа ног", "Учит строить розыгрыш на грунте, выбирать высоту над сеткой и возвращаться в исходную позицию. Нагрузку адаптирует к уровню ученика."),
    ("Айгуль Нурбекова", 7, "Мини-теннис для детей 5–7 лет", "Проводит короткие игровые задания с мягкими мячами и небольшими ракетками. Создаёт спокойную атмосферу и обсуждает прогресс с родителями."),
    ("Павел Крылов", 13, "Групповые занятия среднего уровня", "Организует тренировку так, чтобы каждый участник получал игровое время. Сочетает контроль направления удара, выход к сетке и матчевую практику."),
    ("Наталья Орлова", 6, "Координация и возвращение к занятиям", "Помогает постепенно вернуться к регулярной любительской игре после перерыва. Начинает с умеренного темпа и внимательно следит за самочувствием группы."),
    ("Руслан Каримов", 15, "Учебные сборы и командные соревнования", "Готовит программу тренировочного дня, распределяет игровые задания и проводит разбор матчей. Учит участников поддерживать партнёров по команде."),
    ("Виктория Данилова", 5, "Индивидуальная работа с юниорами", "Помогает закрепить базовые движения и научиться самостоятельно вести счёт. В демонстрационном расписании временно не принимает новые группы."),
)

SERVICES = (
    ("clay-rental", "Аренда грунтового корта", "court rental", "Самостоятельная игра на открытом грунте. Бронирование по часам; доступность зависит от погоды и состояния покрытия.", "court"),
    ("hard-rental", "Аренда крытого корта", "court rental", "Крытый хард для одиночной и парной игры. Время освещения и подготовка площадки включены в учебную стоимость аренды.", "court"),
    ("grass-rental", "Аренда корта с искусственной травой", "court rental", "Открытая площадка для любительских встреч. Администратор подскажет требования к обуви и свободные часы.", "court"),
    ("individual", "Индивидуальная тренировка", "schedule", "Урок один на один с тренером: постановка цели, разминка, техническая часть и закрепление навыка в игре.", "training"),
    ("adult-group", "Группа для взрослых", "schedule", "Занятия для участников близкого уровня подготовки. В программе работа ног, основные удары и короткие учебные матчи.", "training"),
    ("kids-red", "Мини-теннис для детей 5–7 лет", "children's tennis", "Первое знакомство с ракеткой на уменьшенной площадке. Используются мягкие красные мячи и задания на координацию.", "kids"),
    ("kids-orange", "Детская группа 8–10 лет", "children's tennis", "Переход к более длинным розыгрышам с оранжевым мячом. Тренер объясняет счёт, подачу и уважительное поведение на корте.", "kids"),
    ("junior-green", "Тренировки юниоров 11–14 лет", "children's tennis", "Занятия с зелёным мячом и постепенным переходом к стандартному. Особое внимание уделяется выбору позиции и игровой самостоятельности.", "training"),
    ("weekend-camp", "Учебный сбор выходного дня", "team training camps", "Программа из двух тренировочных блоков, перерыва и разбора матчей. Подходит любительской команде с заранее согласованным уровнем.", "club"),
    ("team-camp", "Командный тренировочный сбор", "team training camps", "Несколько дней занятий по согласованному расписанию. Включает технические упражнения, парные встречи и обсуждение командной тактики.", "trophy"),
)

PRICE_CATEGORIES = (
    ("rental", "Аренда кортов"),
    ("training", "Тренировки для взрослых"),
    ("children", "Детские занятия"),
    ("camps", "Учебные и командные сборы"),
)

# category, service, title, KGS, minutes, discount, details
PRICES = (
    ("rental", "clay-rental", "Грунт: будний день до 17:00", "800.00", 60, 0, "Стоимость за корт на один час."),
    ("rental", "clay-rental", "Грунт: вечер и выходные", "1100.00", 60, 0, "Час аренды в часы повышенного спроса."),
    ("rental", "hard-rental", "Крытый хард: утренний час", "1200.00", 60, 0, "Один час до 12:00 в будний день."),
    ("rental", "hard-rental", "Крытый хард: вечерний час", "1600.00", 60, 0, "Аренда после 17:00; освещение включено."),
    ("rental", "grass-rental", "Искусственная трава: дневная игра", "700.00", 60, 0, "Один час самостоятельной игры днём."),
    ("rental", "grass-rental", "Искусственная трава: полтора часа", "1050.00", 90, 0, "Продлённое время для парного матча."),
    ("training", "individual", "Знакомство с тренером", "1000.00", 45, 0, "Вводный индивидуальный урок; аренда корта оплачивается отдельно."),
    ("training", "individual", "Индивидуальный урок: 60 минут", "1800.00", 60, 0, "Работа с тренером; аренда корта оплачивается отдельно."),
    ("training", "individual", "Индивидуальный урок: 90 минут", "2500.00", 90, 0, "Техника и игровая практика; аренда корта оплачивается отдельно."),
    ("training", "individual", "Пакет из четырёх индивидуальных уроков", "6480.00", 240, 10, "Итоговая цена за четыре урока по 60 минут с учётом скидки; аренда отдельно."),
    ("training", "adult-group", "Разовое занятие в группе взрослых", "900.00", 60, 0, "Цена за участника; корт включён."),
    ("training", "adult-group", "Восемь групповых занятий для взрослых", "6480.00", 480, 10, "Восемь занятий по 60 минут; итоговая цена с учётом скидки."),
    ("training", "adult-group", "Групповая матчевая практика", "1200.00", 90, 0, "Учебные геймы и разбор решений; цена за участника."),
    ("children", "kids-red", "Пробное занятие по мини-теннису", "400.00", 40, 0, "Ракетка и мягкие мячи предоставляются на время урока."),
    ("children", "kids-red", "Мини-теннис: восемь занятий", "4800.00", 320, 0, "Восемь уроков по 40 минут в небольшой группе."),
    ("children", "kids-orange", "Оранжевый мяч: разовое занятие", "750.00", 60, 0, "Цена за ребёнка; инвентарь и корт включены."),
    ("children", "kids-orange", "Оранжевый мяч: восемь занятий", "5400.00", 480, 10, "Восемь занятий по 60 минут; итоговая цена с учётом скидки."),
    ("children", "junior-green", "Юниоры: разовая тренировка", "850.00", 75, 0, "Технические упражнения и учебный матч в группе."),
    ("children", "junior-green", "Юниоры: восемь тренировок", "6120.00", 600, 10, "Восемь занятий по 75 минут; итоговая цена с учётом скидки."),
    ("camps", "weekend-camp", "Сбор выходного дня: один участник", "3200.00", 240, 0, "Четыре часа программы с перерывами; проживание и питание не включены."),
    ("camps", "weekend-camp", "Сбор выходного дня: два дня", "6000.00", 480, 0, "Два учебных дня по четыре часа программы; цена за участника."),
    ("camps", "weekend-camp", "Парная практика на сборе", "1800.00", 120, 0, "Двухчасовой учебный блок; цена за участника."),
    ("camps", "team-camp", "Командный сбор: три дня", "12000.00", 720, 0, "Три дня по четыре часа программы; цена за участника без проживания."),
    ("camps", "team-camp", "Командный сбор: пять дней", "19000.00", 1200, 0, "Пять дней по четыре часа программы; проживание и питание отдельно."),
    ("camps", "team-camp", "Командный разбор игровых эпизодов", "2200.00", 90, 0, "Совместный разбор учебных матчей; цена за командный блок."),
)

NEWS = (
    ("open-day", "День знакомства с теннисом", "В учебном клубе подготовлена программа открытого занятия для начинающих.", "Гости смогут познакомиться с устройством корта, попробовать простые упражнения с ракеткой и задать вопросы тренерам. В демонстрационном сценарии участие проходит по предварительной записи, а группы распределяются по возрасту.", "club"),
    ("clay-care", "Как готовят грунтовые корты к игре", "Показываем порядок ухода за покрытием до и после тренировки.", "Сначала сотрудники проверяют влажность грунта, затем выравнивают поверхность и очищают линии. После занятия игроки проходят по корту щёткой; при дожде площадку закрывают до осмотра.", "court"),
    ("adult-start", "Новая группа для взрослых начинающих", "Программа первых занятий посвящена базовым ударам и правилам игры.", "На вводном уроке участники учатся держать ракетку, направлять мяч через сетку и вести счёт. Темп подбирается по группе, а упражнения чередуются с короткими игровыми заданиями.", "training"),
    ("red-ball", "Красный мяч: первые шаги в теннисе", "Мини-теннис помогает детям познакомиться с ракеткой в игровой форме.", "На уменьшенной площадке используются мягкие мячи и невысокая сетка. Короткие задания на ловкость и внимание позволяют менять активность и постепенно привыкать к работе в группе.", "kids"),
    ("doubles", "Парная игра: учимся действовать вместе", "Тематическая тренировка посвящена взаимодействию двух игроков.", "Участники разбирают расположение у сетки, смену сторон и простые сигналы партнёру. В заключительной части проходят учебные геймы с остановками для обсуждения решений.", "training"),
    ("evening-hard", "Вечерние тренировки на крытом харде", "В демонстрационном расписании добавлены занятия после рабочего дня.", "Крытый зал позволяет планировать уроки независимо от осадков. Перед бронированием группа согласует уровень подготовки и продолжительность, чтобы всем хватало времени на практику.", "court"),
    ("racket-choice", "Как подобрать первую ракетку", "Длина, масса и размер ручки влияют на удобство начальных занятий.", "На учебной встрече тренер показывает несколько типов ракеток и объясняет, как оценить хват. Для первого урока можно использовать клубный инвентарь, а решение о покупке принять после знакомства с игрой.", "equipment"),
    ("junior-match", "Юниоры провели учебные матчи", "Сценарий клубной встречи помогает освоить счёт и самостоятельную игру.", "Участники менялись соперниками после коротких сетов и записывали свои наблюдения. Тренеры обсуждали выбор позиции и уважительное общение, не превращая встречу в отборочное соревнование.", "trophy"),
    ("warm-up", "Разминка перед выходом на корт", "Публикуем тему практического занятия по подготовке к игре.", "В учебный комплекс включены лёгкое движение, упражнения на координацию и постепенное увеличение темпа ударов. Программу адаптируют к возрасту и самочувствию участника.", "training"),
    ("family-day", "Семейная встреча на корте", "Для детей и родителей подготовлены совместные игровые задания.", "Семьи смогут пройти эстафету с мячом, попробовать обмен через сетку и сыграть короткий парный матч. Все активности имеют учебный характер, а инвентарь подбирается по возрасту.", "kids"),
    ("weekend-plan", "Программа учебного сбора выходного дня", "Два тренировочных блока дополняются перерывом и обсуждением матчей.", "Утром группа работает над точностью ударов, затем переходит к игровым ситуациям. После отдыха участники пробуют парные комбинации и формулируют личную задачу на следующую тренировку.", "club"),
    ("serve", "Мастерская подачи для любителей", "На тематическом уроке разбирают подброс, ритм и направление мяча.", "Тренер предлагает упражнения без мяча и подачу с сокращённой дистанции. По мере освоения движения участники переходят к полному корту и учатся спокойно начинать розыгрыш.", "training"),
    ("grass", "Знакомство с искусственной травой", "У разных покрытий свои особенности движения и отскока.", "Учебная тренировка начинается с проверки обуви и короткого обмена мячами. Затем группа сравнивает темп розыгрыша с грунтом и хардом и обсуждает подходящую позицию на приёме.", "court"),
    ("ladder", "Клубная лестница для любительских встреч", "Демонстрационный формат помогает найти соперника близкого уровня.", "Участники договариваются о времени матча и заранее выбирают продолжительность игры. Результаты используются для подбора следующих встреч, а спорные эпизоды разбираются в спокойной обстановке.", "trophy"),
    ("orange-ball", "Переход от красного мяча к оранжевому", "Тренеры объясняют родителям, как меняется программа детских занятий.", "Размер площадки и скорость мяча увеличиваются постепенно. Решение о переходе принимается по готовности ребёнка поддерживать розыгрыш, ориентироваться на корте и выполнять задания без спешки.", "kids"),
    ("court-etiquette", "Пять привычек вежливого игрока", "Напоминаем о правилах общения и перемещения между кортами.", "Возвращайте мяч соседям в паузе, предупреждайте партнёра о готовности и уважайте забронированное время. После игры соберите инвентарь и оставьте площадку готовой для следующей пары.", "club"),
    ("video-review", "Разбор учебного матча с тренером", "Новый формат встречи посвящён анализу игровых решений.", "Группа рассматривает заранее согласованные фрагменты тренировки и отмечает удачные действия. Для каждого участника выбирают одну практическую задачу, которую можно проверить на следующем занятии.", "training"),
    ("team-camp", "Командный сбор: от упражнений к матчам", "Учебная программа объединяет техническую работу и парные встречи.", "В начале дня команда согласует цели, затем работает на станциях с разными заданиями. Итоговый блок посвящён матчевой практике и обсуждению того, как помогать партнёрам во время игры.", "trophy"),
    ("equipment-care", "Уход за ракеткой и клубным инвентарём", "Практические советы по хранению чехлов, мячей и ракеток.", "После занятия инвентарь следует просушить и вернуть в предназначенную зону хранения. Состояние обмотки и струн проверяют до игры, а повреждённые мячи откладывают для замены.", "equipment"),
    ("draft-calendar", "Проект календаря следующих клубных встреч", "Черновик учебного расписания подготовлен для внутреннего согласования.", "В проект включены встречи начинающих, семейный формат и парный турнир. Даты и состав групп в этом демонстрационном материале служат примером работы с неопубликованной новостью.", "club"),
)

GALLERY_EXTRA = (
    ("Учебная зона у входа в клуб", "club", "club"),
    ("Место отдыха между тренировками", "club", "club"),
    ("Ракетки перед вводным занятием", "other", "equipment"),
    ("Корзина мячей для отработки ударов", "other", "equipment"),
    ("Разминка группы взрослых", "training", "training"),
    ("Первый обмен через сетку", "training", "training"),
    ("Детские упражнения с красным мячом", "training", "kids"),
    ("Работа ног на учебной площадке", "training", "training"),
    ("Парная тренировка у сетки", "training", "training"),
    ("Награды учебного клубного турнира", "tournaments", "trophy"),
    ("Финальный матч любительской встречи", "tournaments", "trophy"),
    ("Командная встреча выходного дня", "tournaments", "trophy"),
    ("Семейный день с ракетками", "club", "kids"),
    ("Юниоры готовятся к учебному матчу", "training", "training"),
    ("Инвентарь после завершения игрового дня", "other", "equipment"),
)

TOURNAMENTS = (
    ("first-set", "Первый сет: турнир начинающих", -90, 2, "Одиночные встречи для взрослых с небольшим игровым опытом. Короткие сеты и помощь со счётом."),
    ("family-doubles", "Семейный парный день", -60, 1, "Учебные пары из детей и взрослых. Игровые задания чередуются с короткими матчами."),
    ("junior-orange", "Оранжевый мяч: встреча юниоров", -30, 2, "Турнирный опыт для группы 8–10 лет на уменьшенной площадке с оранжевым мячом."),
    ("club-week", "Клубная неделя парной игры", -1, 4, "Текущая учебная встреча любительских пар. Расписание предусматривает групповой этап и матчи за места."),
    ("autumn-cup", "Кубок точной подачи", 7, 2, "Соревнование любителей среднего уровня с акцентом на самостоятельный счёт и уважение к сопернику."),
    ("junior-green", "Зелёный мяч: юниорский старт", 21, 1, "Учебные матчи юниоров 11–14 лет. Формат и продолжительность учитывают возраст участников."),
    ("mixed-doubles", "Микст выходного дня", 45, 2, "Парная встреча смешанных любительских команд. Короткий групповой этап и итоговые матчи."),
    ("team-cup", "Командный кубок учебного клуба", 70, 3, "Проект командного соревнования с одиночными и парными встречами; публикация ожидает согласования."),
)


def _stdlib_png(index, surface):
    """Небольшая теннисная схема в настоящем PNG без сторонних модулей."""
    width, height = 960, 600
    colors = {
        "clay": ((58, 72, 64), (177, 83, 54)),
        "hard": ((31, 70, 74), (47, 113, 153)),
        "artificial_grass": ((33, 69, 61), (78, 124, 77)),
    }
    outer, inner = colors.get(surface, colors["hard"])
    pixels = bytearray(bytes(outer) * width * height)

    def rectangle(x1, y1, x2, y2, color):
        row = bytes(color) * (x2 - x1)
        for y in range(y1, y2):
            offset = (y * width + x1) * 3
            pixels[offset:offset + len(row)] = row

    rectangle(130, 90, 830, 510, inner)
    for x in (130, 190, 770, 826):
        rectangle(x, 90, x + 4, 510, (245, 246, 226))
    for y in (90, 195, 405, 506):
        rectangle(130, y, 830, y + 4, (245, 246, 226))
    rectangle(478, 195, 482, 405, (245, 246, 226))
    rectangle(115, 297, 845, 303, (24, 36, 39))
    cx, cy = 290 + index % 9 * 38, 380 + index % 3 * 16
    for y in range(cy - 18, cy + 19):
        for x in range(cx - 18, cx + 19):
            if (x - cx) ** 2 + (y - cy) ** 2 <= 18 ** 2:
                offset = (y * width + x) * 3
                pixels[offset:offset + 3] = bytes((216, 231, 99))
    raw = b"".join(b"\x00" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"tEXt", b"Description\x00Locally generated fictional tennis club illustration")
        + chunk(b"IDAT", zlib.compress(raw, 8)) + chunk(b"IEND", b"")
    )


def render_image(scene, label, index, surface="hard"):
    """Авторская иллюстрация: корт, инвентарь, кубок или вымышленный тренер."""
    try:
        from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
    except ImportError:
        return _stdlib_png(index, surface)

    width, height = (900, 1100) if scene == "coach" else (1280, 800)
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    palettes = ((18, 47, 50), (28, 50, 69), (55, 57, 47), (47, 52, 69))
    base = palettes[index % len(palettes)]
    for y in range(height):
        t = y / height
        draw.line((0, y, width, y), fill=tuple(int(c + 19 * (1 - t)) for c in base))
    cream = "#f1f0dc"
    lime = "#d5e982"
    draw.ellipse((width - 300, -180, width + 140, 260), fill=tuple(c + 13 for c in base))
    draw.ellipse((-220, height - 180, 260, height + 260), outline=tuple(c + 25 for c in base), width=2)

    fonts = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    )
    font_path = next((path for path in fonts if path.is_file()), None)

    def font(size):
        return ImageFont.truetype(str(font_path), size) if font_path else ImageFont.load_default()

    def text(position, value, size, fill=cream):
        if font_path is None:
            value = value.encode("ascii", "replace").decode("ascii")
        draw.text(position, value, font=font(size), fill=fill)

    def ball(cx, cy, radius, color=lime):
        draw.ellipse((cx - radius + 5, cy - radius + 9, cx + radius + 5, cy + radius + 9), fill="#172f34")
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)
        draw.arc((cx - radius * 1.45, cy - radius, cx + radius * .25, cy + radius), -75, 75, fill=cream, width=max(2, radius // 12))
        draw.arc((cx - radius * .25, cy - radius, cx + radius * 1.45, cy + radius), 105, 255, fill=cream, width=max(2, radius // 12))

    def racket(cx, cy, scale=1):
        rx, ry = int(78 * scale), int(104 * scale)
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill="#284b50", outline=cream, width=max(3, int(9 * scale)))
        for dx in range(-rx + 12, rx, max(8, int(14 * scale))):
            span = int(ry * math.sqrt(max(0, 1 - (dx / rx) ** 2)))
            draw.line((cx + dx, cy - span + 5, cx + dx, cy + span - 5), fill="#8ca79d", width=1)
        for dy in range(-ry + 12, ry, max(8, int(14 * scale))):
            span = int(rx * math.sqrt(max(0, 1 - (dy / ry) ** 2)))
            draw.line((cx - span + 5, cy + dy, cx + span - 5, cy + dy), fill="#8ca79d", width=1)
        draw.line((cx - rx // 2, cy + ry - 8, cx, cy + ry + int(65 * scale)), fill=cream, width=max(3, int(7 * scale)))
        draw.line((cx + rx // 2, cy + ry - 8, cx, cy + ry + int(65 * scale)), fill=cream, width=max(3, int(7 * scale)))
        draw.line((cx, cy + ry + int(58 * scale), cx, cy + ry + int(160 * scale)), fill="#c88962", width=max(6, int(22 * scale)))

    def court():
        surface_color = {"clay": "#b86d4b", "hard": "#497c99", "artificial_grass": "#63885f"}[surface]
        left_top, right_top = (365, 220), (915, 220)
        left_bottom, right_bottom = (140, 650), (1140, 650)
        draw.polygon(((315, 195), (965, 195), (1220, 695), (60, 695)), fill="#38645a")
        draw.polygon((left_top, right_top, right_bottom, left_bottom), fill=surface_color)

        def point(u, v):
            left = 365 - 225 * v
            right = 915 + 225 * v
            return (int(left + (right - left) * u), int(220 + 430 * v))

        for u in (0, .125, .875, 1):
            draw.line((point(u, 0), point(u, 1)), fill=cream, width=3)
        for v in (0, .26, .74, 1):
            draw.line((point(0, v), point(1, v)), fill=cream, width=3)
        draw.line((point(.5, .26), point(.5, .74)), fill=cream, width=3)
        a, b = point(-.04, .5), point(1.04, .5)
        draw.polygon((a, b, (b[0], b[1] - 55), (a[0], a[1] - 55)), fill="#284447")
        for x in range(a[0], b[0], 16):
            draw.line((x, a[1], x, a[1] - 55), fill="#8ba49a", width=1)
        for dy in (12, 24, 36, 48):
            draw.line((a[0], a[1] - dy, b[0], b[1] - dy), fill="#8ba49a", width=1)
        draw.line((a[0], a[1] - 55, b[0], b[1] - 55), fill=cream, width=5)
        for p in (a, b):
            draw.line((p[0], p[1] + 8, p[0], p[1] - 66), fill=cream, width=6)
        ball(330 + index % 7 * 67, 545 + index % 3 * 18, 17)

    def player(cx, cy, color, small=False):
        size = .75 if small else 1
        draw.ellipse((cx - 15 * size, cy - 52 * size, cx + 15 * size, cy - 22 * size), fill="#dbaf87")
        draw.polygon(((cx - 20 * size, cy - 19 * size), (cx + 20 * size, cy - 19 * size), (cx + 25 * size, cy + 27 * size), (cx - 22 * size, cy + 27 * size)), fill=color)
        draw.line((cx - 12 * size, cy + 27 * size, cx - 25 * size, cy + 65 * size), fill=cream, width=8)
        draw.line((cx + 12 * size, cy + 27 * size, cx + 36 * size, cy + 57 * size), fill=cream, width=8)
        draw.line((cx + 18 * size, cy - 10 * size, cx + 45 * size, cy - 28 * size), fill="#dbaf87", width=7)

    text((54, 32), "СЕТ  /  УЧЕБНЫЙ ТЕННИСНЫЙ КЛУБ", 22, lime)
    if scene == "coach":
        skin_colors = ("#d4a47b", "#be8965", "#e2b991", "#c79a76")
        skin = skin_colors[index % len(skin_colors)]
        shirt = ("#9baec6", "#d0bf94", "#97b8a3", "#c29b87")[index % 4]
        draw.ellipse((120, 145, 780, 805), fill=tuple(c + 20 for c in base))
        draw.rounded_rectangle((190, 532, 710, 1010), radius=130, fill=shirt)
        draw.polygon(((355, 540), (450, 645), (545, 540)), fill=cream)
        draw.rounded_rectangle((395, 430, 505, 565), radius=35, fill=skin)
        if index % 2 == 0:
            draw.rounded_rectangle((285, 235, 615, 585), radius=125, fill="#443d38")
        draw.ellipse((300, 234, 600, 503), fill=skin)
        draw.pieslice((293, 205, 607, 397), 180, 355, fill="#443d38")
        draw.arc((345, 319, 400, 344), 190, 340, fill="#514239", width=5)
        draw.arc((500, 319, 555, 344), 200, 350, fill="#514239", width=5)
        for x in (377, 523):
            draw.ellipse((x - 5, 352, x + 5, 363), fill="#3e3d36")
        draw.line((450, 363, 440, 401, 456, 404), fill="#a77559", width=4)
        draw.arc((407, 393, 496, 452), 15, 165, fill="#84584c", width=4)
        draw.line((303, 687, 283, 960), fill=cream, width=3)
        racket(659, 664, .68)
        ball(259, 823, 48)
        draw.rectangle((0, 900, width, height), fill=base)
        text((54, 930), label.split()[0], 38)
        text((54, 980), " ".join(label.split()[1:]), 36)
        text((54, 1044), "Вымышленный тренер • иллюстрация", 19, lime)
    else:
        if scene in ("court", "club", "training", "kids"):
            court()
            if scene in ("training", "kids"):
                player(505, 560, "#e5bd86", small=scene == "kids")
                player(755, 310, lime, small=scene == "kids")
            if scene == "club":
                draw.rounded_rectangle((64, 210, 270, 365), radius=12, fill="#81988c")
                draw.rectangle((80, 234, 254, 248), fill=cream)
                for x in (92, 155, 218):
                    draw.rectangle((x, 273, x + 29, 322), fill="#284b50")
        elif scene == "equipment":
            draw.ellipse((270, 630, 1000, 710), fill="#203a3e")
            racket(480, 344, 1.3)
            racket(780, 378, .95)
            ball(870, 592, 72)
            ball(1030, 627, 40)
            ball(328, 617, 33)
        elif scene == "trophy":
            gold = "#dcbd77"
            draw.ellipse((350, 618, 930, 697), fill="#203a3e")
            draw.arc((369, 235, 581, 464), 60, 300, fill=gold, width=23)
            draw.arc((699, 235, 911, 464), 240, 480, fill=gold, width=23)
            draw.polygon(((485, 233), (795, 233), (747, 416), (685, 467), (595, 467), (533, 416)), fill=gold)
            draw.rectangle((617, 455, 663, 563), fill=gold)
            draw.rounded_rectangle((540, 550, 740, 595), radius=12, fill=gold)
            draw.rounded_rectangle((504, 592, 776, 649), radius=8, fill="#5d766d")
            text((606, 286), "1", 100, "#fff1c4")
            ball(900, 591, 49)
            racket(303, 399, .65)

        draw.rectangle((0, 686, width, height), fill=base)
        size = 35
        while size > 18 and draw.textbbox((0, 0), label, font=font(size))[2] > width - 108:
            size -= 1
        text((54, 701), label, size)
        text((54, 757), "ДЕМОНСТРАЦИОННАЯ ИЛЛЮСТРАЦИЯ  •  ВЫМЫШЛЕННЫЙ КЛУБ", 18, lime)

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Title", label)
    metadata.add_text("Description", DEMO_NOTE)
    metadata.add_text("Source", "Original procedural illustration generated locally by seed_data.py")
    metadata.add_text("Asset", f"{scene}-{index}-{surface}")
    output = io.BytesIO()
    image.save(output, format="PNG", pnginfo=metadata, optimize=True)
    return output.getvalue()


class Command(BaseCommand):
    help = "Добавляет вымышленные теннисные данные и PNG в media/seed_data/, не обновляя существующие записи."

    def handle(self, *args, **options):
        self.created = Counter()
        self.existing = Counter()
        self.failed = Counter()
        self.created_files = []
        self.created_objects = []
        self.errors = []
        self._preflight()
        self.stdout.write(DEMO_NOTE)
        self.stdout.write(f"Дата учебного календаря: {timezone.localdate().isoformat()}; цены указаны в сомах (KGS).")
        self.stdout.write("Изображения: локальные PNG-иллюстрации, без скачивания и установки зависимостей.")
        try:
            with transaction.atomic():
                self._seed()
                self._verify_created()
        except Exception as exc:
            self._cleanup(self.created_files[:])
            raise CommandError(f"Заполнение отменено, добавление записей откачено: {exc}") from exc

        self.stdout.write("\nМодель               Новых   Найдено   Пропущено   Всего в БД")
        for model in MODELS:
            name = model.__name__
            self.stdout.write(
                f"{name:<20} {self.created[name]:>5} {self.existing[name]:>9}"
                f" {self.failed[name]:>11} {model.objects.count():>13}"
            )
        self.stdout.write(f"Сохранено новых изображений: {len(self.created_files)}")
        if self.errors:
            for error in self.errors:
                self.stderr.write(self.style.WARNING(error))
            raise CommandError("Безопасная часть заполнения завершена; причины пропусков перечислены выше.")
        self.stdout.write(self.style.SUCCESS(
            f"Готово. Новых записей: {sum(self.created.values())}. "
            "Существующие записи и изображения не изменялись."
        ))

    def _preflight(self):
        """Проверить существующую схему и место хранения до первого INSERT."""
        db_config = connection.settings_dict
        if db_config["ENGINE"] == "django.db.backends.sqlite3":
            name = str(db_config["NAME"])
            if name == ":memory:" or not Path(name).is_file():
                raise CommandError("Существующая SQLite-база не найдена. Команда не создаёт БД и не выполняет миграции.")
        try:
            with connection.cursor() as cursor:
                tables = set(connection.introspection.table_names(cursor))
                for model in MODELS:
                    table = model._meta.db_table
                    if table not in tables:
                        raise CommandError(f"Отсутствует таблица {table}. Схема БД не изменялась.")
                    columns = {column.name for column in connection.introspection.get_table_description(cursor, table)}
                    missing = {field.column for field in model._meta.concrete_fields} - columns
                    if missing:
                        raise CommandError(f"В {table} отсутствуют столбцы: {', '.join(sorted(missing))}. Схема БД не изменялась.")
        except DatabaseError as exc:
            raise CommandError(f"Не удалось прочитать существующую БД: {exc}") from exc

        media_root = (Path(settings.BASE_DIR) / "media").resolve()
        if Path(settings.MEDIA_ROOT).resolve() != media_root:
            raise CommandError("MEDIA_ROOT отличается от media/ проекта. Запись за пределами media/seed_data/ запрещена.")
        seed_root = media_root / "seed_data"
        if seed_root.resolve() != seed_root:
            raise CommandError("media/seed_data/ содержит символьную ссылку; изображения не сохранялись.")
        for model in MODELS:
            for field in model._meta.fields:
                if isinstance(field, models.ImageField):
                    storage = field.storage
                    if not isinstance(storage, FileSystemStorage) or Path(storage.location).resolve() != media_root:
                        raise CommandError(f"Хранилище {model.__name__}.{field.name} не указывает на media/ проекта.")
                    if getattr(storage, "_allow_overwrite", False):
                        raise CommandError("Хранилище допускает перезапись изображений. Заполнение не выполнялось.")

    def _cleanup(self, files):
        """Удалить только файлы, впервые созданные текущей неудачной операцией."""
        for storage, name in reversed(files):
            try:
                storage.delete(name)
                self.created_files.remove((storage, name))
            except (OSError, ValueError) as exc:
                self.stderr.write(self.style.WARNING(f"Не удалось убрать новый файл {name}: {exc}"))

    def _skip(self, model, reason):
        self.failed[model.__name__] += 1
        self.errors.append(f"{model.__name__}: {reason}")
        return None

    def _create(self, model, lookup, values, images=None):
        """Валидация и get_or_create без вызова save для найденных объектов."""
        files = []
        try:
            with transaction.atomic():
                matches = model.objects.filter(**lookup).order_by("pk")
                existing = matches.first()
                if existing is not None:
                    self.existing[model.__name__] += 1
                    if matches.count() > 1:
                        self.stderr.write(self.style.WARNING(
                            f"{model.__name__}: уже существуют совпадающие записи {lookup}; использована первая, данные не изменялись."
                        ))
                    return existing

                values = dict(values)
                obj = model(**lookup, **values)
                obj.full_clean()
                for field_name, specification in (images or {}).items():
                    storage = model._meta.get_field(field_name).storage
                    key = hashlib.sha256(
                        f"{model._meta.label_lower}:{lookup}:{field_name}".encode("utf-8")
                    ).hexdigest()[:16]
                    folder = f"seed_data/{model._meta.model_name}"
                    # Проверка каждого вложенного пути исключает выход через symlink.
                    target = Path(storage.path(folder))
                    if target.resolve() != target:
                        raise ValueError(f"Небезопасный путь изображения: {folder}")
                    content = ContentFile(render_image(*specification))
                    name = storage.save(f"{folder}/{key}-{field_name}.png", content)
                    files.append((storage, name))
                    self.created_files.append((storage, name))
                    values[field_name] = name
                    setattr(obj, field_name, name)
                obj.full_clean()
                obj, created = model.objects.get_or_create(**lookup, defaults=values)
                if created:
                    self.created[model.__name__] += 1
                    self.created_objects.append(obj)
                else:
                    self._cleanup(files)
                    self.existing[model.__name__] += 1
                return obj
        except (ValidationError, DatabaseError, OSError, ValueError) as exc:
            self._cleanup(files)
            return self._skip(model, f"{lookup}: {exc}")

    def _verify_created(self):
        for obj in self.created_objects:
            obj.full_clean()
            for field in obj._meta.fields:
                if isinstance(field, models.ImageField):
                    value = getattr(obj, field.name)
                    if not value or not value.name.startswith("seed_data/") or not value.storage.exists(value.name):
                        raise CommandError(f"Не найдено изображение {obj._meta.label}.{field.name}, pk={obj.pk}.")

    def _seed(self):
        if ClubInfo.objects.exists() and not ClubInfo.objects.filter(pk=1).exists():
            self._skip(ClubInfo, "Уже есть информация о клубе с pk != 1. Особый save() не позволяет безопасно добавить singleton.")
        else:
            self._create(ClubInfo, {"pk": 1}, {
                "name": "Теннисный клуб «Сет» — учебный пример",
                "description": "Вымышленный клуб для знакомства с теннисом: открытые и крытые корты, занятия для детей и взрослых, любительские встречи. " + DEMO_NOTE,
                "hero_title": "Ваш первый сет начинается здесь",
                "address": "Учебный адрес: г. Бишкек, ул. Теннисная, 10 (вымышленный)",
                "phone": None, "email": "info@tennis-demo.example", "tg_url": "",
            }, {"hero_image": ("club", "Теннис начинается с первого удара", 0),
                "about_image": ("training", "Встречаемся на корте", 1)})

        for index, (title, content) in enumerate(RULES, 1):
            self._create(ClubRule, {"title": title}, {"content": content, "order": index, "is_active": True})

        court_types = {}
        for index, (key, name, surface, indoor, description) in enumerate(COURT_TYPES):
            court_types[key] = self._create(CourtType, {"slug": f"demo-tennis-{key}"}, {
                "name": name, "description": description + " " + DEMO_NOTE,
                "surface": surface, "is_indoor": indoor,
            }, {"image": ("court", name, index, surface)})

        courts = {}
        for number in range(1, 16):
            key = ("clay", "hard", "grass")[(number - 1) // 5]
            court_type = court_types[key]
            if court_type is None:
                self._skip(Court, f"Корт № {number}: тип {key} недоступен.")
                continue
            courts[number] = self._create(Court, {"court_number": number}, {
                "court_type": court_type, "is_active": number != 15,
                "description": f"Корт № {number}. {COURT_NOTES[number - 1]} {DEMO_NOTE}",
            })

        for index, (name, experience, specialization, bio) in enumerate(COACHES, 1):
            self._create(Coach, {"full_name": name}, {
                "short_bio": bio + " " + DEMO_NOTE, "experience": experience,
                "specialization": specialization, "order": index, "is_active": index != 12,
            }, {"photo": ("coach", name, index)})

        services = {}
        for index, (key, title, category, description, scene) in enumerate(SERVICES, 1):
            surface = {"clay-rental": "clay", "grass-rental": "artificial_grass"}.get(key, "hard")
            services[key] = self._create(Service, {"slug": f"demo-tennis-{key}"}, {
                "title": title, "description": description + " " + DEMO_NOTE,
                "category": category, "is_active": True, "order": index,
            }, {"image": (scene, title, index, surface)})

        categories = {}
        for index, (key, title) in enumerate(PRICE_CATEGORIES, 1):
            categories[key] = self._create(PriceCategory, {"slug": f"demo-tennis-{key}"}, {
                "title": title, "order": index,
            })

        for category_key, service_key, title, price, minutes, discount, description in PRICES:
            category = categories[category_key]
            service = services[service_key]
            if category is None or service is None:
                self._skip(PriceItem, f"{title}: недоступна категория или услуга.")
                continue
            self._create(PriceItem, {"category": category, "title": title}, {
                "service": service, "description": description + " Учебный тариф в сомах (KGS), не публичная оферта.",
                "price": Decimal(price), "duration_minutes": minutes,
                "discount_percent": discount, "is_active": True,
            })

        for index, (key, title, short, content, scene) in enumerate(NEWS, 1):
            self._create(News, {"slug": f"demo-tennis-{key}"}, {
                "title": title, "short_description": short,
                "content": content + "\n\n" + DEMO_NOTE,
                "is_published": index != len(NEWS),
            }, {"image": (scene, title, index, ("clay", "hard", "artificial_grass")[index % 3])})

        for number in range(1, 16):
            court = courts.get(number)
            if court is None:
                self._skip(GalleryImage, f"Недоступен корт № {number} для иллюстрации.")
                continue
            surface = court.court_type.surface
            self._create(GalleryImage, {"title": f"Учебная галерея: корт № {number}"}, {
                "category": "courts", "courts": court, "order": number,
            }, {"image": ("court", f"Корт № {number} • {court.court_type.name}", number, surface)})

        for index, (title, category, scene) in enumerate(GALLERY_EXTRA, 16):
            self._create(GalleryImage, {"title": "Учебная галерея: " + title[0].lower() + title[1:]}, {
                "category": category, "courts": None, "order": index,
            }, {"image": (scene, title, index)})

        today = timezone.localdate()
        for index, (key, title, offset, days, description) in enumerate(TOURNAMENTS, 1):
            start = today + timedelta(days=offset)
            end = start + timedelta(days=days - 1)
            status = "finished" if end < today else "upcoming" if start > today else "ongoing"
            self._create(Tournament, {"slug": f"demo-tennis-{key}"}, {
                "title": title, "description": description + " " + DEMO_NOTE,
                "start_date": start, "end_date": end, "status": status,
                "is_published": index != len(TOURNAMENTS),
            }, {"image": ("trophy", title, index)})
