import pandas as pd


def load_sales_data(file_path):
    REQUIRED_COLS = [
    "ID операции",
    "Дата",
    "Адрес магазина",
    "Район магазина",
    "Артикул",
    "Название товара",
    "Отдел товара",
    "Количество упаковок, шт.",
    "Операция",
    "Цена руб./шт."
    ]
    try:
        data = pd.read_csv(file_path, sep=";", encoding="utf-8")
    except Exception:
        try:
            data = pd.read_csv(file_path, sep=";", encoding="cp1251")
        except Exception:
            print(f"Не удалось прочесть файл, проверьте кодировку и разделитель: {file_path}")
            return None

    missing = [col for col in REQUIRED_COLS if col not in data.columns]
    if missing:
        print(f"Не удалось прочесть файл: {file_path}. Отсутстуют обязательные столбцы: {', '.join(missing)}")
        return None

    return data



def preprocess_data(data):
    if data is None:
        return None

    data_clean = data.copy()

    data_clean["Дата"] = pd.to_datetime(
        data_clean["Дата"], errors="coerce", dayfirst=True
    )

    data_clean["Количество упаковок, шт."] = pd.to_numeric(
        data_clean["Количество упаковок, шт."], errors="coerce"
    )

    data_clean["Цена руб./шт."] = (
        data_clean["Цена руб./шт."].astype(str).str.replace(",", ".", regex=False)
    )
    data_clean["Цена руб./шт."] = pd.to_numeric(
        data_clean["Цена руб./шт."], errors="coerce"
    )

    before = len(data_clean)
    data_clean = data_clean.dropna()
    removed = before - len(data_clean)

    if removed > 0:
        print(f"Удалено строк с пустыми значениями: {removed}")

    data_clean["Сумма операции"] = (
        data_clean["Количество упаковок, шт."] * data_clean["Цена руб./шт."]
    )

    return data_clean



def get_operational_data(data_clean, operation_type=None):
    if operation_type is None:
        return data_clean.copy()
    
    operation_type_lower = operation_type.lower()
    filtered_data = data_clean[data_clean['Операция'].str.lower() == operation_type_lower].copy()
    
    return filtered_data



def calculate_revenue_by_period(data_clean, period='D'):
    sales_data = get_operational_data(data_clean, operation_type="Продажа")
        
    if period == 'W':
        revenue_by_period = sales_data.groupby(pd.Grouper(key='Дата', freq='W-MON'))['Сумма операции'].sum().reset_index()
        revenue_by_period.columns = ['Дата', 'Выручка по периоду']
    else:
        revenue_by_period = sales_data.groupby(pd.Grouper(key='Дата', freq=period))['Сумма операции'].sum().reset_index()
        revenue_by_period.columns = ['Дата', 'Выручка по периоду'] 
        
    revenue_by_period = revenue_by_period.sort_values('Дата')
    revenue_by_period = revenue_by_period.reset_index(drop=True)
        
    return revenue_by_period



def calculate_profit_by_period(data_clean, period='D'):
    sales_data = get_operational_data(data_clean, operation_type="Продажа")
    if sales_data is None or len(sales_data) == 0:
        print("Нет данных о продажах для расчета доходов")
        return None
    
    expense_operations = ["Поступление"]
    
    if expense_operations:
        expense_data = data_clean[data_clean['Операция'].str.lower().isin(expense_operations)].copy()
    else:
        expense_data = data_clean[data_clean['Операция'].str.lower() != "продажа"].copy()
    
    if period == 'W':
        income_by_period = sales_data.groupby(pd.Grouper(key='Дата', freq='W-MON'))['Сумма операции'].sum()
    else:
        income_by_period = sales_data.groupby(pd.Grouper(key='Дата', freq=period))['Сумма операции'].sum()
    
    if len(expense_data) > 0:
        if period == 'W':
            expense_by_period = expense_data.groupby(pd.Grouper(key='Дата', freq='W-MON'))['Сумма операции'].sum()
        else:
            expense_by_period = expense_data.groupby(pd.Grouper(key='Дата', freq=period))['Сумма операции'].sum()
    else:
        expense_by_period = pd.Series(0, index=income_by_period.index)
        print("Внимание: данные о расходах не найдены. Прибыль рассчитывается как выручка.")
    
    profit_data = pd.DataFrame({
        'Доходы': income_by_period,
        'Расходы': expense_by_period
    }).fillna(0)
    
    profit_data['Прибыль по периоду'] = profit_data['Доходы'] - profit_data['Расходы']
    
    profit_result = profit_data[['Прибыль по периоду']].reset_index()
    profit_result.columns = ['Дата', 'Прибыль по периоду']
    profit_result = profit_result.sort_values('Дата').reset_index(drop=True)
    
    return profit_result



def aggregate_sales_by_category(data_clean):
    sales_data = get_operational_data(data_clean, operation_type="Продажа")
    
    agg_dict = {}
    if 'Сумма операции' in sales_data.columns:
        agg_dict['Выручка'] = ('Сумма операции', 'sum')
    if 'Количество упаковок, шт.' in sales_data.columns:
        agg_dict['Проданных единиц'] = ('Количество упаковок, шт.', 'sum')
    if 'Артикул' in sales_data.columns:
        agg_dict['Уникальных товаров'] = ('Артикул', 'nunique')
    
    sales_by_category = sales_data.groupby('Отдел товара').agg(**agg_dict)
    
    category_stats = sales_by_category.sort_index()
    
    return category_stats



def get_top_n_products(data_clean, n=5, metric='quantity', date='all'):
    sales_data = get_operational_data(data_clean, "Продажа")

    if date != 'all':
        sales_data = sales_data[sales_data["Дата"] == date]

    if metric == 'quantity':
        agg_column = 'Количество упаковок, шт.'
        result_column = f'Сумма_{agg_column}'
        agg_func = 'sum'
    elif metric == 'revenue':
        agg_column = 'Сумма операции'
        result_column = f'Сумма_{agg_column}'
        agg_func = 'sum'
    else:
        return None
        
    grouped_data = sales_data.groupby('Название товара', as_index=False).agg({agg_column: agg_func}).rename(columns={agg_column: result_column})

    data_sorted = grouped_data.sort_values(by=result_column, ascending=False)
    return data_sorted.head(n).reset_index(drop=True)



def analyze_inventory_turnover(data_clean, top_n=10):
    sales_data = get_operational_data(data_clean, 'Продажа')
    purchases_data = get_operational_data(data_clean, 'Поступление')

    sales_grouped = sales_data.groupby(['Артикул', 'Название товара']).agg({
        'Количество упаковок, шт.': 'sum',
        'Сумма операции': 'sum'}).reset_index()
    sales_grouped = sales_grouped.rename(columns={
        'Количество упаковок, шт.': 'Продано_упаковок',
        'Сумма операции': 'Выручка_от_продаж'})
    
    purchases_grouped = purchases_data.groupby(['Артикул', 'Название товара']).agg({
        'Количество упаковок, шт.': 'sum',
        'Сумма операции': 'sum'}).reset_index()
    purchases_grouped = purchases_grouped.rename(columns={
        'Количество упаковок, шт.': 'Поступлено_упаковок',
        'Сумма операции': 'Затраты_на_закупки'})
    
    inventory_analysis = pd.merge(
        sales_grouped,
        purchases_grouped,
        on=['Артикул', 'Название товара'],
        how='outer')
    
    inventory_analysis['Продано_упаковок'] = inventory_analysis['Продано_упаковок'].fillna(0)
    inventory_analysis['Выручка_от_продаж'] = inventory_analysis['Выручка_от_продаж'].fillna(0)
    inventory_analysis['Поступлено_упаковок'] = inventory_analysis['Поступлено_упаковок'].fillna(0)
    inventory_analysis['Затраты_на_закупки'] = inventory_analysis['Затраты_на_закупки'].fillna(0)

    inventory_analysis['Разница_упаковок'] = (
        inventory_analysis['Продано_упаковок'] - inventory_analysis['Поступлено_упаковок'])

    inventory_analysis['Прибыль'] = (
        inventory_analysis['Выручка_от_продаж'] - inventory_analysis['Затраты_на_закупки'])

    mask = inventory_analysis['Затраты_на_закупки'] > 0
    inventory_analysis['Рентабельность_%'] = 0
    inventory_analysis.loc[mask, 'Рентабельность_%'] = ((inventory_analysis.loc[mask, 'Прибыль'] / inventory_analysis.loc[mask, 'Затраты_на_закупки']) * 100)
    only_sales_mask = (inventory_analysis['Продано_упаковок'] > 0) & (inventory_analysis['Затраты_на_закупки'] == 0)
    inventory_analysis.loc[only_sales_mask, 'Рентабельность_%'] = None


    inventory_analysis['Абс_разница'] = inventory_analysis['Разница_упаковок'].abs()
    inventory_analysis = inventory_analysis.sort_values('Абс_разница', ascending=False)
    inventory_analysis = inventory_analysis.drop('Абс_разница', axis=1)
    
    numeric_cols = ['Продано_упаковок', 'Поступлено_упаковок', 'Разница_упаковок']
    for col in numeric_cols:
        inventory_analysis[col] = inventory_analysis[col].astype(int)
    money_cols = ['Выручка_от_продаж', 'Затраты_на_закупки', 'Прибыль']
    for col in money_cols:
        inventory_analysis[col] = inventory_analysis[col].round(2)
    inventory_analysis['Рентабельность_%'] = inventory_analysis['Рентабельность_%'].round(2)
    
    return inventory_analysis.head(top_n).reset_index(drop=True)



def get_inventory_insights(inventory_analysis):
    insights = {
        'overstock_candidates': [],
        'understock_candidates': [],
        'most_profitable': [],
        'least_profitable': [],
        'summary_stats': {}
    }
    
    overstock_threshold = inventory_analysis['Продано_упаковок'].mean() * 0.3
    overstock_items = inventory_analysis[inventory_analysis['Разница_упаковок'] > overstock_threshold]

    understock_threshold = -inventory_analysis['Продано_упаковок'].mean() * 0.3
    understock_items = inventory_analysis[inventory_analysis['Разница_упаковок'] < understock_threshold]
   
    most_profitable = inventory_analysis.nlargest(5, 'Прибыль')
    least_profitable = inventory_analysis.nsmallest(5, 'Прибыль')

    insights['overstock_candidates'] = overstock_items[[
        'Артикул', 'Название товара', 'Разница_упаковок', 
        'Продано_упаковок', 'Поступлено_упаковок'
    ]].to_dict('records')
    insights['understock_candidates'] = understock_items[[
        'Артикул', 'Название товара', 'Разница_упаковок',
        'Продано_упаковок', 'Поступлено_упаковок'
    ]].to_dict('records')
    insights['most_profitable'] = most_profitable[[
        'Артикул', 'Название товара', 'Прибыль', 
        'Рентабельность_%', 'Выручка_от_продаж', 'Затраты_на_закупки'
    ]].to_dict('records')
    insights['least_profitable'] = least_profitable[[
        'Артикул', 'Название товара', 'Прибыль',
        'Рентабельность_%', 'Выручка_от_продаж', 'Затраты_на_закупки'
    ]].to_dict('records')

    insights['summary_stats'] = {
        'total_revenue': inventory_analysis['Выручка_от_продаж'].sum(),
        'total_costs': inventory_analysis['Затраты_на_закупки'].sum(),
        'total_profit': inventory_analysis['Прибыль'].sum(),
        'avg_profitability': inventory_analysis['Рентабельность_%'].mean(),
        'items_with_deficit': len(overstock_items),
        'items_with_excess': len(understock_items),
        'total_items': len(inventory_analysis)
    }
    
    return insights
