import streamlit as st
import numpy as np
import pandas as pd
import math
from models.room import Room
from models.material import Material
from data.materials_database import load_materials, load_surface_materials, get_materials_by_surface_type
from utils.acoustic_calculations import calculate_structural_reverberation_time, calculate_combined_reverberation_time
from utils.export_results import export_calculation_results_to_excel
import matplotlib.pyplot as plt
def main():
    st.set_page_config(
        page_title="Расчет времени реверберации",
        page_icon="🔊",
        layout="wide"
    )
    
    st.title("🔊 Расчет времени реверберации помещений")
    st.markdown("*Расчет по методике СП 415.1325800.2018 «Здания общественные. Правила акустического проектирования»*")
    
    # Sidebar for room information
    with st.sidebar:
        st.header("📋 Данные помещения")
        
        room_name = st.text_input("Наименование помещения", value="", placeholder="Например: Конференц-зал")
        room_purpose = st.selectbox(
            "Назначение помещения",
            [
                "Выберите назначение",
                "Конференц-зал",
                "Аудитория",
                "Концертный зал",
                "Театральный зал",
                "Кинотеатр",
                "Спортивный зал",
                "Офисное помещение",
                "Ресторан",
                "Другое"
            ]
        )
        
        if room_purpose == "Другое":
            room_purpose = st.text_input("Укажите назначение", placeholder="Введите назначение помещения")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📐 Геометрические размеры")
        
        # Выбор режима ввода размеров
        size_input_mode = st.radio(
            "Способ задания размеров:",
            ["📏 Стандартные размеры (длина × ширина × высота)", "📐 Ручной ввод площадей поверхностей"],
            help="Выберите способ задания геометрии помещения"
        )
        
        manual_wall_area = None
        manual_floor_area = None
        manual_ceiling_area = None
        length = None
        width = None
        height = None
        
        if size_input_mode == "📏 Стандартные размеры (длина × ширина × высота)":
            # Стандартный режим ввода
            length = st.number_input("Длина (м)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1)
            width = st.number_input("Ширина (м)", min_value=0.1, max_value=1000.0, value=8.0, step=0.1)
            height = st.number_input("Высота (м)", min_value=0.1, max_value=100.0, value=3.5, step=0.1)
            
            # Calculate derived values
            calculated_volume = length * width * height
            wall_area = 2 * (length * height + width * height)
            floor_area = length * width
            ceiling_area = length * width
            total_surface_area = wall_area + floor_area + ceiling_area
            
            st.info(f"**Расчетные площади:**")
            st.info(f"• Стены: {wall_area:.2f} м²")
            st.info(f"• Пол: {floor_area:.2f} м²") 
            st.info(f"• Потолок: {ceiling_area:.2f} м²")
            
        else:
            # Режим ручного ввода площадей
            st.markdown("**Введите площади поверхностей:**")
            manual_wall_area = st.number_input("Площадь стен (м²)", min_value=0.1, max_value=10000.0, value=100.0, step=0.1)
            manual_floor_area = st.number_input("Площадь пола (м²)", min_value=0.1, max_value=10000.0, value=80.0, step=0.1)
            manual_ceiling_area = st.number_input("Площадь потолка (м²)", min_value=0.1, max_value=10000.0, value=80.0, step=0.1)
            
            total_surface_area = manual_wall_area + manual_floor_area + manual_ceiling_area
            
            # Для расчета объема все равно нужны размеры
            st.markdown("**Для расчета объема введите размеры:**")
            length = st.number_input("Длина (м)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key="manual_length")
            width = st.number_input("Ширина (м)", min_value=0.1, max_value=1000.0, value=8.0, step=0.1, key="manual_width")
            height = st.number_input("Высота (м)", min_value=0.1, max_value=100.0, value=3.5, step=0.1, key="manual_height")
            
            calculated_volume = length * width * height
            
        # Option for manual volume correction
        manual_volume = st.checkbox("✏️ Ручная корректировка объема")
        
        if manual_volume:
            volume = st.number_input(
                "Объем помещения (м³)", 
                min_value=0.1, 
                max_value=100000.0, 
                value=calculated_volume, 
                step=0.1,
                help="Скорректированный объем с учетом особенностей помещения"
            )
            if abs(volume - calculated_volume) > 0.1:
                st.warning(f"⚠️ Расчетный объем: {calculated_volume:.2f} м³, указанный: {volume:.2f} м³")
        else:
            volume = calculated_volume
        
        st.info(f"**Объем помещения:** {volume:.2f} м³")
        st.info(f"**Общая площадь поверхностей:** {total_surface_area:.2f} м²")
    
    with col2:
        st.subheader("🏗️ Материалы поверхностей")
        
        # Initialize materials lists if not in session state
        if 'structural_materials' not in st.session_state:
            st.session_state.structural_materials = []
        if 'acoustic_materials' not in st.session_state:
            st.session_state.acoustic_materials = []
        
        # Category and surface type selection outside of form to allow dynamic updates
        material_category = st.selectbox(
            "Категория материала",
            ["Ограждающие конструкции", "Акустические конструкции"]
        )
        
        surface_type = st.selectbox(
            "Тип поверхности",
            ["Стены", "Потолок", "Пол", "Остекление", "Двери", "Стулья", "Все"]
        )

        MATERIALS_DATABASE = load_materials("data/materials.json")
        SURFACE_MATERIALS = load_surface_materials("data/surface_materials.json")
        # Получаем материалы для выбранного типа поверхности
        available_materials = get_materials_by_surface_type(SURFACE_MATERIALS, surface_type)
        if not available_materials:
            available_materials = list(MATERIALS_DATABASE.keys())
        
        # Material input form
        with st.form("add_material_form"):
            material_name = st.selectbox(
                "Материал",
                available_materials
            )
            
            area = st.number_input("Площадь (м²)", min_value=0.01, max_value=10000.0, value=1.0, step=0.01)
            
            submitted = st.form_submit_button("➕ Добавить материал")
            
            if submitted and material_name and area > 0:
                material_data = {
                    'name': material_name,
                    'surface_type': surface_type,
                    'area': area,
                    'category': material_category,
                    'absorption_coefficients': MATERIALS_DATABASE[material_name]
                }
                
                if material_category == "Ограждающие конструкции":
                    st.session_state.structural_materials.append(material_data)
                else:
                    st.session_state.acoustic_materials.append(material_data)
                
                st.rerun()
    
    # Display added materials in two sections
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.structural_materials:
            st.subheader("🏢 Ограждающие конструкции")
            
            structural_data = []
            for i, material_data in enumerate(st.session_state.structural_materials):
                structural_data.append({
                    "№": i + 1,
                    "Поверхность": material_data['surface_type'],
                    "Материал": material_data['name'],
                    "Площадь (м²)": f"{material_data['area']:.2f}"
                })
            
            df_structural = pd.DataFrame(structural_data)
            st.dataframe(df_structural, use_container_width=True, hide_index=True)
            
            # Remove structural material buttons
            if len(st.session_state.structural_materials) > 0:
                cols = st.columns(min(len(st.session_state.structural_materials), 5))
                for i, col in enumerate(cols):
                    if i < len(st.session_state.structural_materials):
                        if col.button(f"Удалить ОК-{i+1}", key=f"remove_struct_{i}"):
                            st.session_state.structural_materials.pop(i)
                            st.rerun()
            
            if st.button("🗑️ Очистить ОК", key="clear_structural"):
                st.session_state.structural_materials = []
                st.rerun()
    
    with col2:
        if st.session_state.acoustic_materials:
            st.subheader("🎧 Акустические конструкции")
            
            acoustic_data = []
            for i, material_data in enumerate(st.session_state.acoustic_materials):
                acoustic_data.append({
                    "№": i + 1,
                    "Поверхность": material_data['surface_type'],
                    "Материал": material_data['name'],
                    "Площадь (м²)": f"{material_data['area']:.2f}"
                })
            
            df_acoustic = pd.DataFrame(acoustic_data)
            st.dataframe(df_acoustic, use_container_width=True, hide_index=True)
            
            # Remove acoustic material buttons
            if len(st.session_state.acoustic_materials) > 0:
                cols = st.columns(min(len(st.session_state.acoustic_materials), 5))
                for i, col in enumerate(cols):
                    if i < len(st.session_state.acoustic_materials):
                        if col.button(f"Удалить АК-{i+1}", key=f"remove_acoustic_{i}"):
                            st.session_state.acoustic_materials.pop(i)
                            st.rerun()
            
            if st.button("🗑️ Очистить АК", key="clear_acoustic"):
                st.session_state.acoustic_materials = []
                st.rerun()
    
    # Calculate button and results
    st.divider()
    
    if st.button("🧮 Рассчитать время реверберации", type="primary", use_container_width=True):
        if not room_name:
            st.error("Введите наименование помещения")
        elif room_purpose == "Выберите назначение":
            st.error("Выберите назначение помещения")
        elif not st.session_state.structural_materials:
            st.error("Добавьте хотя бы одну ограждающую конструкцию")
        else:
            # Create room object
            room = Room(
                name=room_name,
                purpose=room_purpose,
                length=length,
                width=width,
                height=height,
                manual_wall_area=manual_wall_area,
                manual_floor_area=manual_floor_area,
                manual_ceiling_area=manual_ceiling_area,
                manual_volume=volume if manual_volume else None
            )
            
            # Add structural materials to room
            for material_data in st.session_state.structural_materials:
                material = Material(
                    name=material_data['name'],
                    surface_type=material_data['surface_type'],
                    area=material_data['area'],
                    absorption_coefficients=material_data['absorption_coefficients'],
                    category=material_data['category']
                )
                room.add_material(material)
                
            # Add acoustic materials to room (if any)
            for material_data in st.session_state.acoustic_materials:
                material = Material(
                    name=material_data['name'],
                    surface_type=material_data['surface_type'],
                    area=material_data['area'],
                    absorption_coefficients=material_data['absorption_coefficients'],
                    category=material_data['category']
                )
                room.add_material(material)
            
            try:
                # Perform structural calculations
                structural_results = calculate_structural_reverberation_time(room)
                
                # Perform combined calculations if acoustic materials exist
                combined_results = None
                if st.session_state.acoustic_materials:
                    combined_results = calculate_combined_reverberation_time(room)
                
                # Store results in session state for export
                st.session_state.calculation_results = {
                    'room_data': {
                        'name': room_name,
                        'purpose': room_purpose,
                        'length': length,
                        'width': width,
                        'height': height,
                        'volume': room.volume,
                        'total_surface_area': room.total_surface_area
                    },
                    'structural_results': structural_results,
                    'combined_results': combined_results,
                    'structural_materials': st.session_state.structural_materials,
                    'acoustic_materials': st.session_state.acoustic_materials
                }
                
                # Store for immediate access
                st.session_state.current_structural_results = structural_results
                st.session_state.current_combined_results = combined_results
                
                # Display results
                st.success("✅ Расчет выполнен успешно!")

                #Графики
                # Частоты
                frequencies = [125, 250, 500, 1000, 2000, 4000]
                
                # Времена реверберации
                #min_times = [structural_results['min_reverberation'][f] for f in frequencies]  # нужно добавить в calculate_structural
               # max_times = [structural_results['max_reverberation'][f] for f in frequencies]
                #structural_times = [structural_results['reverberation_times'][f] for f in frequencies]
               # combined_times = [combined_results['reverberation_times'][f] for f in frequencies] if combined_results else None
                
               # plt.figure(figsize=(10,5))
               # plt.plot(frequencies, min_times, 'g--', marker='o', label="Минимальное время")
               # plt.plot(frequencies, max_times, 'g-.', marker='o', label="Максимальное время")
               # plt.plot(frequencies, structural_times, 'r-o', label="Исходное время (ОК)")
               # if combined_times:
               #     plt.plot(frequencies, combined_times, 'b-o', label="Итоговое время (с АК)")
                
              #  plt.xlabel("Частота (Гц)")
               # plt.ylabel("Время реверберации (с)")
               # plt.title("Время реверберации по частотам")
               # plt.grid(True)
              #  plt.legend()
             #   st.pyplot(plt)

                
                # Экспорт Excel
                if 'calculation_results' in st.session_state:
                    try:
                        excel_file = export_calculation_results_to_excel(
                            room_data=st.session_state.calculation_results['room_data'],
                            structural_results=structural_results,
                            combined_results=combined_results,
                            structural_materials=st.session_state.calculation_results['structural_materials'],
                            acoustic_materials=st.session_state.calculation_results['acoustic_materials']
                        )
                        clean_filename = room_name.replace(' ', '_').replace('/', '_').replace('\\', '_') or "Расчет"
                        st.download_button(
                            label="💾 Скачать Excel-отчет",
                            data=excel_file.getvalue(),
                            file_name=f"Акустический_расчет_{clean_filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Ошибка при создании файла: {type(e).__name__} — {str(e)}")
                
                # Critical frequency and basic metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="Критическая частота",
                        value=f"{structural_results['critical_frequency']:.1f} Гц"
                    )
                
                with col2:
                    st.metric(
                        label="Объем помещения",
                        value=f"{volume:.2f} м³"
                    )
                
                with col3:
                    st.metric(
                        label="Общая площадь поверхностей",
                        value=f"{total_surface_area:.2f} м²"
                    )
                
                # Results display tabs
                if combined_results:
                    tab1, tab2 = st.tabs(["🏢 Ограждающие конструкции", "🎧 С акустическими материалами"])
                    
                    with tab1:
                        _display_calculation_results(structural_results, "⏱️ Время реверберации (только ОК)")
                    
                    with tab2:
                        _display_calculation_results(combined_results, "⏱️ Время реверберации (с АК)")
                    
                   # with tab3:
                      #  _display_comparison_results(structural_results, combined_results)
                else:
                    _display_calculation_results(structural_results, "⏱️ Время реверберации по частотам")
                
                # Additional information
                if structural_results['critical_frequency'] > 125:
                    st.warning("⚠️ Критическая частота больше 125 Гц. Результат для частоты 125 Гц следует считать ориентировочным.")
                
                # Detailed calculations expander
                with st.expander("🔍 Подробные расчеты"):
                    st.write("**Коэффициенты звукопоглощения материалов:**")
                    
                    frequencies = [125, 250, 500, 1000, 2000, 4000]
                    detailed_data = []
                    # Combine both structural and acoustic materials for display
                    all_materials = st.session_state.structural_materials + st.session_state.acoustic_materials
                    
                    for material_data in all_materials:
                        row = {
                            "Категория": material_data['category'],
                            "Материал": material_data['name'],
                            "Поверхность": material_data['surface_type'],
                            "Площадь (м²)": f"{material_data['area']:.2f}"
                        }
                        for freq in frequencies:
                            row[f"{freq} Гц"] = f"{material_data['absorption_coefficients'][freq]:.3f}"
                        detailed_data.append(row)
                    
                    detailed_df = pd.DataFrame(detailed_data)
                    st.dataframe(detailed_df, use_container_width=True, hide_index=True)
                    
                    st.write("**Формулы расчета:**")
                    st.latex(r"f_{кр} = \frac{1770}{\sqrt{V}}")
                    st.latex(r"T = \frac{0.163 \cdot V}{S \cdot \varphi(\alpha_{ср})} \text{ (125-1000 Гц)}")
                    st.latex(r"T = \frac{0.163 \cdot V}{S \cdot \varphi(\alpha_{ср}) + nV} \text{ (2000-4000 Гц)}")
                    st.latex(r"\varphi(\alpha_{ср}) = -\ln(1 - \alpha_{ср})")
                    st.latex(r"\alpha_{ср} = \frac{A_{общ}}{S}")
                    
                    # Пример расчета для одной частоты
                    st.write("**Пример полного расчета для частоты 125 Гц:**")
                    
                    # Берем данные для примера расчета
                    example_freq = 125
                    example_volume = volume
                    example_surface_area = total_surface_area
                    
                    # Рассчитываем компоненты для примера
                    if all_materials:
                        example_absorption_area = 0
                        st.write("*Расчет эквивалентной площади звукопоглощения:*")
                        
                        # Считаем все материалы, но показываем детально только первые 3
                        displayed_count = 0
                        for material_data in all_materials:
                            absorption_coeff = material_data['absorption_coefficients'][example_freq]
                            material_absorption = material_data['area'] * absorption_coeff
                            example_absorption_area += material_absorption
                            
                            if displayed_count < 10:
                                st.write(f"• {material_data['name']}: {material_data['area']:.2f} м² × {absorption_coeff:.3f} = {material_absorption:.3f} м²")
                                displayed_count += 1
                        
                        if len(all_materials) > 10:
                            remaining_absorption = 0
                            for material_data in all_materials[10:]:
                                absorption_coeff = material_data['absorption_coefficients'][example_freq]
                                material_absorption = material_data['area'] * absorption_coeff
                                remaining_absorption += material_absorption
                            st.write(f"• ... и еще {len(all_materials) - 10} материал(ов): {remaining_absorption:.3f} м²")
                        
                        # Добавочное звукопоглощение
                        if example_freq < 500:
                            additional_coeff = 0.09
                        else:
                            additional_coeff = 0.05
                        
                        # Вычисляем площадь пола для добавочного звукопоглощения
                        if size_input_mode == "📏 Стандартные размеры (длина × ширина × высота)":
                            floor_area = length * width
                        else:
                            floor_area = manual_floor_area if manual_floor_area is not None else 80.0
                        
                        additional_absorption = additional_coeff * floor_area
                        total_absorption_area = example_absorption_area + additional_absorption
                        
                        st.write(f"• Добавочное звукопоглощение: {floor_area:.2f} м² (площадь пола) × {additional_coeff:.2f} = {additional_absorption:.2f} м²")
                        st.write(f"• **Общая ЭПЗ:** {total_absorption_area:.2f} м²")
                        
                        # Средний КЗП с учетом эффективной площади для структурных материалов
                        has_acoustic_materials = len(st.session_state.acoustic_materials) > 0
                        if has_acoustic_materials:
                            # Вычисляем эффективную площадь (за вычетом акустических материалов)
                            acoustic_area_total = sum(mat['area'] for mat in st.session_state.acoustic_materials)
                            effective_surface_area = example_surface_area - acoustic_area_total
                            st.write(f"*Эффективная площадь поверхностей (для ОК):*")
                            st.write(f"Эффективная площадь = {example_surface_area:.2f} - {acoustic_area_total:.2f} = {effective_surface_area:.2f} м²")
                        else:
                            effective_surface_area = example_surface_area
                            
                        avg_alpha = total_absorption_area / effective_surface_area
                        st.write(f"*Средний коэффициент звукопоглощения:*")
                        st.write(f"αср = {total_absorption_area:.2f} / {effective_surface_area:.2f} = {avg_alpha:.4f}")
                        
                        # Функция φ(αср)
                        phi_value = -math.log(1 - min(avg_alpha, 0.99))
                        st.write(f"*Функция φ(αср):*")
                        st.write(f"φ(αср) = -ln(1 - {avg_alpha:.4f}) = {phi_value:.4f}")
                        
                        # Время реверберации
                        denominator = effective_surface_area * phi_value
                        reverb_time = (0.163 * example_volume) / denominator
                        
                        st.write(f"*Время реверберации:*")
                        st.write(f"T = (0.163 × {example_volume:.2f}) / ({effective_surface_area:.2f} × {phi_value:.4f})")
                        st.write(f"T = {0.163 * example_volume:.2f} / {denominator:.2f} = **{reverb_time:.3f} с**")
                    else:
                        st.write("*Для отображения примера добавьте материалы*")
                
            except Exception as e:
                st.error(f"Ошибка при расчете: {str(e)}")
                st.error("Проверьте правильность введенных данных")

def _display_calculation_results(results, title):
    """Отображение результатов расчета"""
    st.subheader(title)
    
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    reverberation_data = []
    
    for freq in frequencies:
        row_data = {
            "Частота (Гц)": freq,
            "Время реверберации (с)": f"{results['reverberation_times'][freq]:.3f}",
            "Средний КЗП": f"{results['average_absorption_coefficients'][freq]:.3f}",
            "ЭПЗ общая (м²)": f"{results['equivalent_absorption_areas'][freq]:.2f}"
        }
        
        # Добавляем дополнительные столбцы для комбинированного расчета
        if 'structural_absorption_areas' in results:
            row_data["ЭПЗ ОК (м²)"] = f"{results['structural_absorption_areas'][freq]:.2f}"
            row_data["ЭПЗ АК (м²)"] = f"{results['acoustic_absorption_areas'][freq]:.2f}"
        
        reverberation_data.append(row_data)
    
    results_df = pd.DataFrame(reverberation_data)
    st.dataframe(results_df, use_container_width=True, hide_index=True)

#def _display_comparison_results(structural_results, combined_results):
#    """Отображение сравнения результатов"""
 #   st.subheader("📊 Сравнение результатов")
    
  #  frequencies = [125, 250, 500, 1000, 2000, 4000]
  #  comparison_data = []
    
  #  for freq in frequencies:
     #   structural_time = structural_results['reverberation_times'][freq]
   #     combined_time = combined_results['reverberation_times'][freq]
    #    difference = structural_time - combined_time
      #  percentage = (difference / structural_time) * 100 if structural_time > 0 else 0
        
     #   comparison_data.append({
      #      "Частота (Гц)": freq,
    #       "Время ОК (с)": f"{structural_time:.3f}",
     #       "Время с АК (с)": f"{combined_time:.3f}",
      #      "Разность (с)": f"{difference:.3f}",
      #      "Снижение (%)": f"{percentage:.1f}%"
      #  })
    
   # comparison_df = pd.DataFrame(comparison_data)
   # st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Эффективность акустических материалов
 #   avg_reduction = sum([
 #       (structural_results['reverberation_times'][freq] - combined_results['reverberation_times'][freq]) / 
 #       structural_results['reverberation_times'][freq] * 100 
  #      for freq in frequencies
 #   ]) / len(frequencies)
    
  #  if avg_reduction > 0:
   #     st.success(f"✅ Среднее снижение времени реверберации: {avg_reduction:.1f}%")
   #     if avg_reduction > 20:
  #          st.info("🎯 Отличная эффективность акустических материалов!")
   #     elif avg_reduction > 10:
   #         st.info("👍 Хорошая эффективность акустических материалов")
   #     else:
   #         st.warning("⚠️ Низкая эффективность акустических материалов")
  #  else:
    #    st.warning("⚠️ Акустические материалы не показывают эффективности")

if __name__ == "__main__":
    main()
