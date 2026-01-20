from datetime import datetime # Импортируем datetime для записи файла
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from process import load_sales_data, preprocess_data, calculate_profit_by_period, aggregate_sales_by_category, get_top_n_products, calculate_revenue_by_period, get_inventory_insights, analyze_inventory_turnover

def present_revenue_by_period(data, period='D'):
    revenue_data = calculate_revenue_by_period(data, period)
    
    if period == 'D':
        labels = revenue_data['Дата'].dt.strftime('%Y-%m-%d')
        title_period = "дням"
    elif period == 'W':
        labels = ["Неделя " + str(i+1) for i in range(len(revenue_data))]
        title_period = "неделям"
    else:
        labels = revenue_data['Дата'].dt.strftime('%Y-%m')
        title_period = "месяцам"
    
    values = revenue_data['Выручка по периоду']
    
    plt.figure(figsize=(10, 8))
    
    colors = sns.color_palette("husl", len(values))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    
    plt.title(f'Распределение выручки по {title_period}', fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.show()



def visualize_category_analysis(data_clean):
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    category_stats = aggregate_sales_by_category(data_clean)
    if category_stats is None or len(category_stats) == 0:
        print("Нет данных для визуализации")
        return None
    
    num_metrics = len(category_stats.columns)
    if num_metrics == 0:
        return None
    
    fig, axes = plt.subplots(1, num_metrics, figsize=(5*num_metrics, 6))
    if num_metrics == 1:
        axes = [axes]
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(category_stats)))
    
    for i, metric in enumerate(category_stats.columns):
        axes[i].bar(category_stats.index, category_stats[metric], color=colors)
        axes[i].set_title(f'{metric.replace("_", " ").title()} по категориям', fontweight='bold')
        axes[i].set_ylabel(metric)
        axes[i].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()



def analyze_real_data(cleaned_data, period):
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    print("="*40)
    
    print("\n" + "="*40)
    print("АНАЛИЗ 1: ПРИБЫЛЬ ПО ПЕРИОДАМ")
    print("="*40)
    
    profit_daily = calculate_profit_by_period(cleaned_data, period)
    if profit_daily is not None:
        print("Прибыль по дням (первые 10 строк):")
        print(profit_daily.head(10))
        
        plt.figure(figsize=(12, 6))
        plt.plot(profit_daily['Дата'], profit_daily['Прибыль по периоду'], marker='o', linewidth=2)
        plt.title('Динамика прибыли по дням', fontweight='bold')
        plt.xlabel('Дата')
        plt.ylabel('Прибыль, руб.')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        
        print(f"\nСтатистика прибыли:")
        print(f"Максимальная прибыль: {profit_daily['Прибыль по периоду'].max():.2f} руб.")
        print(f"Минимальная прибыль: {profit_daily['Прибыль по периоду'].min():.2f} руб.")
        print(f"Средняя прибыль: {profit_daily['Прибыль по периоду'].mean():.2f} руб.")
        print(f"Общая прибыль: {profit_daily['Прибыль по периоду'].sum():.2f} руб.")
    else:
        print("Не удалось рассчитать прибыль")
    
    print("\n" + "="*50)
    print("АНАЛИЗ 2: СТАТИСТИКА ПО КАТЕГОРИЯМ")
    print("="*50)
    
    category_stats = aggregate_sales_by_category(cleaned_data)
    if category_stats is not None and len(category_stats) > 0:
        print("Статистика по категориям:")
        print(category_stats)
        
        if 'выручка' in category_stats.columns:
            print(f"\nОбщая выручка: {category_stats['выручка'].sum():.2f} руб.")
        if 'проданных единиц' in category_stats.columns:
            print(f"Общее количество проданных единиц: {category_stats['проданных единиц'].sum():.0f} шт.")
        if 'уникальных товаров' in category_stats.columns:
            print(f"Всего уникальных товаров: {category_stats['уникальных товаров'].sum():.0f} шт.")
        
        if 'выручка' in category_stats.columns:
            top_categories = category_stats.nlargest(3, 'выручка')
            print(f"\nТоп-3 категории по выручке:")
            for i, (category, row) in enumerate(top_categories.iterrows(), 1):
                print(f"{i}. {category}: {row['выручка']:.2f} руб.")
    else:
        print("Не удалось рассчитать статистику по категориям")



def present_top_n_products(data, n, metric, date):
    df = get_top_n_products(data, n, metric, date)

    # Используем вертикальные столбцы вместо горизонтальных
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = sns.color_palette("husl", n)
    
    if metric == 'revenue':
        bars = ax.bar(df["Название товара"], df["Сумма_Сумма операции"], edgecolor='black', color=colors)
        ax.set_title("Топ самых продаваемых товаров по выручке")
        ax.set_ylabel("Рублей")
    else:
        bars = ax.bar(df["Название товара"], df["Сумма_Количество упаковок, шт."], edgecolor='black', color=colors)
        ax.set_title("Топ самых продаваемых товаров по количеству")
        ax.set_ylabel("Упаковок")
    
    # Поворачиваем подписи по оси X на 45 градусов
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()



def print_inventory_report(data, top_n):
    inventory_analysis = analyze_inventory_turnover(data, top_n)
    insights = get_inventory_insights(inventory_analysis)
    
    # Генерируем имя файла с текущей датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inventory_report_{timestamp}.txt"
    
    # Открываем файл для записи
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 40 + "\n")
        f.write("АНАЛИЗ ДВИЖЕНИЯ ТОВАРОВ И ИХ РЕНТАБЕЛЬНОСТИ\n")
        f.write("=" * 40 + "\n")
        
        f.write("\n СВОДНАЯ СТАТИСТИКА:\n")
        f.write("-" * 40 + "\n")
        stats = insights['summary_stats']
        f.write(f"Всего товаров в анализе: {stats['total_items']}\n")
        f.write(f"Общая выручка: {stats['total_revenue']:,.2f} руб.\n")
        f.write(f"Общие затраты на закупки: {stats['total_costs']:,.2f} руб.\n")
        f.write(f"Общая прибыль: {stats['total_profit']:,.2f} руб.\n")
        f.write(f"Средняя рентабельность: {stats['avg_profitability']:.2f}%\n")
        f.write(f"Товаров с возможным дефицитом: {stats['items_with_deficit']}\n")
        f.write(f"Товаров с возможным излишком: {stats['items_with_excess']}\n")
        
        f.write("\n ТОВАРЫ С ВОЗМОЖНЫМ ДЕФИЦИТОМ (продажи > поступления):\n")
        f.write("-" * 40 + "\n")
        if insights['overstock_candidates']:
            for item in insights['overstock_candidates'][:5]:
                f.write(f"• {item['Название товара']} ({item['Артикул']})\n")
                f.write(f"  Продано: {item['Продано_упаковок']} уп., Поступило: {item['Поступлено_упаковок']} уп.\n")
                f.write(f"  Разница: +{item['Разница_упаковок']} уп. (дефицит)\n")
        else:
            f.write("Нет товаров с явным дефицитом\n")
        
        f.write("\n ТОВАРЫ С ВОЗМОЖНЫМ ИЗЛИШКОМ (поступления > продаж):\n")
        f.write("-" * 40 + "\n")
        if insights['understock_candidates']:
            for item in insights['understock_candidates'][:5]:
                f.write(f"• {item['Название товара']} ({item['Артикул']})\n")
                f.write(f"  Продано: {item['Продано_упаковок']} уп., Поступило: {item['Поступлено_упаковок']} уп.\n")
                f.write(f"  Разница: {item['Разница_упаковок']} уп. (излишек)\n")
        else:
            f.write("Нет товаров с явным излишком\n")
        
        f.write("\n САМЫЕ ПРИБЫЛЬНЫЕ ТОВАРЫ:\n")
        f.write("-" * 40 + "\n")
        for item in insights['most_profitable']:
            f.write(f"• {item['Название товара']} ({item['Артикул']})\n")
            f.write(f"  Прибыль: {item['Прибыль']:,.2f} руб. | "
                   f"Рентабельность: {item['Рентабельность_%']}%\n")
        
        f.write("\n НАИМЕНЕЕ ПРИБЫЛЬНЫЕ ТОВАРЫ:\n")
        f.write("-" * 40 + "\n")
        for item in insights['least_profitable']:
            profitability = item['Рентабельность_%']
            profit_status = f"Прибыль: {item['Прибыль']:,.2f} руб." if item['Прибыль'] >= 0 else f"Убыток: {item['Прибыль']:,.2f} руб."
            f.write(f"• {item['Название товара']} ({item['Артикул']})\n")
            f.write(f"  {profit_status} | Рентабельность: {profitability}%\n")
        
        f.write("\n" + "=" * 40 + "\n")
    
    # Выводим сообщение в консоль
    print(f"Анализ товаров произведен успешно. Результаты записаны в файл: {filename}")



def get_user_request():
    print('=' * 40)
    print("Вас приветствует визуализатор продаж.")
    print("Он поможет Вам загрузить файл и построить отчёты/графики.")
    print('=' * 40)
    print()

    file_path = input("Введите путь к файлу CSV (например: Данные 1.csv): ").strip()

    data = load_sales_data(file_path)
    data_clean = preprocess_data(data)

    if data_clean is None:
        print("Не получилось загрузить данные. Завершаю программу.")
        return
    
    while True:
        while True:
            print('=' * 40)
            print("Выберите функцию из списка ниже: ")
            print("1. Посчитать выручку за период.")
            print("2. Посчитать прибыль за период.")
            print("3. Сгруппировать продажи по отделам.")
            print("4. Получить топ самых продаваемых товаров.")
            print("5. Проанализировать движение товаров.")
            print('=' * 40)
            user_request = input("Введите число, соответствующее выбранной функции: ")
            if user_request in [str(x) for x in range(1, 6)]:
                print()
                break
            else:
                print("Функция введена неверно, попробуйте еще раз.")
        
        if user_request == '1':
            while True:
                print("\nВыберите период для анализа выручки:")
                print("1. По дням")
                print("2. По неделям") 
                print("3. По месяцам")
                period_choice = input("Введите число (1-3): ")
                
                if period_choice == '1':
                    period = 'D'
                    period_name = "дням"
                    break
                elif period_choice == '2':
                    period = 'W'
                    period_name = "неделям"
                    break
                elif period_choice == '3':
                    period = 'M'
                    period_name = "месяцам"
                    break
                else:
                    print("Некорректный выбор. Пожалуйста, введите число от 1 до 3.")
            
            print(f"\nСтрою круговую диаграмму распределения выручки по {period_name}...")
            present_revenue_by_period(data_clean, period)

        if user_request == '2':
            while True:
                print("\nВыберите период для анализа прибыли:")
                print("1. По дням")
                print("2. По неделям") 
                print("3. По месяцам")
                period_choice = input("Введите число (1-3): ")
                
                if period_choice == '1':
                    period = 'D'
                    period_name = "дням"
                    break
                elif period_choice == '2':
                    period = 'W'
                    period_name = "неделям"
                    break
                elif period_choice == '3':
                    period = 'M'
                    period_name = "месяцам"
                    break
                else:
                    print("Некорректный выбор. Пожалуйста, введите число от 1 до 3.")
            
            print(f"\nСтрою визуализацию распределения выручки по {period_name}...")
            analyze_real_data(data_clean, period)

        if user_request == '3':
            print("Представляю анализ по категориям.")
            visualize_category_analysis(data_clean)

        if user_request == '4':
            while True:
                try:
                    n = int(input("Сколько самых продаваемых товаров вы хотите увидеть? --- "))
                    if n <= 0:
                        raise ValueError
                    break
                except:
                    print("Пожалуйста, введите целое положительное число")
            
            while True:
                available_metrics = {
                    '1' : 'quantity',
                    '2' : 'revenue'
                }
                s = input("По какому параметру составить топ (введите число): количество (1) или выручка (2)? --- ")
                if s in available_metrics.keys():
                    metric = available_metrics[s]
                    break
                else:
                    print("Что-то пошло не так, попробуйте еще раз.")
            
            while True:
                s = input("По какой дате составить топ? Введите дату в формате 'ГГГГ-ММ-ДД' или '0' если хотите получить информацию за весь период. --- ")
                if s == "0":
                    date = 'all'
                    break
                elif s in data_clean["Дата"].unique():
                    date = s
                    break
                else:
                    print("Дата введена некорректно, попробуйте еще раз.")
            print(f"\nСтрою столбчатую диаграмму {n} самых продаваемый товаров по {'выручке' if metric == 'quantity' else 'количеству'} за {'весь период' if date == 'all' else date}...")
            present_top_n_products(data_clean, n, metric, date)
        
        if user_request == '5':
            while True:
                try:
                    n = int(input("Сколько товаров вывести в отчете? --- "))
                    if n <= 0:
                        raise ValueError
                    break
                except:
                    print("Пожалуйста, введите целое положительное число")

            print_inventory_report(data_clean, n)


        print()
        print('=' * 40)
        again = input("Хотите сделать что-то еще? (да/нет): ").strip().lower()

        if again == "да":
            continue
        elif again == "нет":
            print('=' * 40)
            print("Принято. Спасибо за использование. Программа завершена. До свидания!")
            print('=' * 40)
            break
        else:
            print('=' * 40)
            print("Не понял Ваш ответ. Завершаю программу. До свидания.")
            print('=' * 40)
            break