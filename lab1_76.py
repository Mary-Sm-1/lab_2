import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO

url = "https://raw.githubusercontent.com/dm-fedorov/python_basic/master/data/opendata.stat"
df = pd.read_csv(StringIO(requests.get(url).text))


df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

pension_keywords = ['пенси', 'пенс', 'пенсион', 'pension', 'выплат пенс']
mask_region = df['region'] == 'Забайкальский край'
mask_year = df['year'] == 2018

filtered = df[mask_region & mask_year].copy()

pension_mask = filtered['name'].str.contains('|'.join(pension_keywords), case=False, na=False)

if pension_mask.any():
    pension_data = filtered[pension_mask].copy()
    
    pension_data['value'] = pd.to_numeric(pension_data['value'], errors='coerce')
    
    daily_pension = pension_data.groupby('date')['value'].mean().reset_index()
    daily_pension = daily_pension.sort_values('date')
    
    # Вычисляем общее среднее значение
    overall_avg = daily_pension['value'].mean()
    
    print(f"ОБЩЕЕ СРЕДНЕЕ ЗНАЧЕНИЕ ПЕНСИИ ЗА 2018 ГОД: {overall_avg:.2f}")
    print()
    
    plt.figure(figsize=(14, 8))
    
    plt.plot(daily_pension['date'], daily_pension['value'], 
             marker='o', linestyle='-', linewidth=2, markersize=8,
             color='darkblue', alpha=0.8, label='Средняя пенсия по дате')

    plt.axhline(y=overall_avg, color='red', linestyle='--', linewidth=2,
                alpha=0.7, label=f'Общее среднее: {overall_avg:.2f}')
    
    plt.title('Изменение среднего значения пенсии в Забайкальском крае, 2018 год',
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Дата', fontsize=12)
    plt.ylabel('Среднее значение пенсии', fontsize=12)
    
    plt.grid(True, alpha=0.3, linestyle='--')
    
    plt.legend(fontsize=11)
    
    plt.gcf().autofmt_xdate()
    
    for i, (date, value) in enumerate(zip(daily_pension['date'], daily_pension['value'])):
        plt.annotate(f'{value:.1f}', 
                     xy=(date, value), 
                     xytext=(0, 10),
                     textcoords='offset points',
                     ha='center',
                     fontsize=9,
                     color='darkblue')
    
    plt.tight_layout()
    
    plt.savefig('pension_trend_2018.png', dpi=150, bbox_inches='tight')
 
    plt.show()
    
else:
    print("=" * 70)
    print("ВНИМАНИЕ: Данные о пенсиях не найдены!")
    print("=" * 70)
    
    print("Доступные показатели в Забайкальском крае за 2018 год:")
    print("-" * 50)
    
    unique_indicators = filtered['name'].unique()
    for i, indicator in enumerate(unique_indicators[:20]):  # Покажем первые 20
        print(f"{i+1}. {indicator}")
    
    if len(unique_indicators) > 20:
        print(f"... и еще {len(unique_indicators) - 20} показателей")
    
    print("-" * 50)

    print("\nСовет: Попробуйте найти данные по другим ключевым словам")

