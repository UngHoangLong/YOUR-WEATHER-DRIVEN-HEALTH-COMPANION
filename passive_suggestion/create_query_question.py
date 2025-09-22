from rag.rule_based import interpret_daily_data_for_single_user_city
import os
import asyncio
from typing import Dict, List
import json
from deep_translator import GoogleTranslator

def make_query_question(user_city_data: dict) -> str:
    """
    Creates a single query string for vector database retrieval, combining
    interpreted daily data with user's disease information.

    Args:
        user_city_data (dict): A dictionary representing a single user-city pair
                               with their daily data.

    Returns:
        str: The complete query string.
    """
    # Get the list of interpreted strings for each period
    list_interpret_for_each_period = interpret_daily_data_for_single_user_city(user_city_data)
    
    # Concatenate the interpreted strings into a single paragraph
    daily_interpretation = "\n".join(list_interpret_for_each_period)
    
    # Get the disease name and description
    disease_name = user_city_data.get('disease_name', 'disease')
    describe_disease_vi = user_city_data.get('describe_disease', 'no detailed description')

    try:
        # Translate from Vietnamese (vi) to English (en)
        translator = GoogleTranslator(source='vi', target='en')
        describe_disease_en = translator.translate(describe_disease_vi)
    except Exception as e:
        # In trường hợp dịch lỗi, sử dụng nội dung gốc
        print(f"[TRANSLATION ERROR] Failed to translate: {e}")
        describe_disease_en = describe_disease_vi

    # Build the complete query question in English
    query_question = (
        f"Based on the following weather, climate, and UV information for each period:\n\n"
        f"*** {daily_interpretation} ***\n\n"
        f"How would this information affect the disease '{disease_name}' with the detailed disease description as follows: '{describe_disease_en}'."
    )
    
    return query_question, describe_disease_en