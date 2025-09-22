import json

def interpret_weather(weather_data: dict) -> str:
    """
    Interprets all weather data parameters into a descriptive text.
    
    Args:
        weather_data (dict): A dictionary containing all weather details.
        
    Returns:
        str: A comprehensive text interpretation of the weather conditions.
    """
    temp = weather_data.get("temp")
    feels_like = weather_data.get("feels_like")
    humidity = weather_data.get("humidity")
    pop = weather_data.get("pop")
    wind_speed = weather_data.get("wind_speed")
    wind_gust = weather_data.get("wind_gust")
    visibility = weather_data.get("visibility")
    clouds_all = weather_data.get("clouds_all")
    weather_main = weather_data.get("weather_main")
    weather_description = weather_data.get("weather_description")
    
    interpretations = []

    # Temperature and Feels Like
    interpretations.append(f"The air temperature is {temp}°C, but it feels like {feels_like}°C.")
    if 20 <= feels_like <= 28:
        interpretations.append("The perceived temperature is very pleasant, ideal for outdoor activities.")
    elif feels_like > 35:
        interpretations.append("The perceived temperature is very hot. Be cautious of heatstroke.")
    elif feels_like > 28:
        interpretations.append("The perceived temperature is quite hot.")
    elif feels_like < 15:
        interpretations.append("The perceived temperature is quite cold. You should dress warmly.")

    # Humidity
    if 40 <= humidity <= 70:
        interpretations.append(f"The humidity is at an ideal level ({humidity}%), providing fresh air.")
    elif humidity > 80:
        interpretations.append(f"The humidity is high ({humidity}%), making the air quite humid.")
    elif humidity < 40:
        interpretations.append(f"The humidity is low ({humidity}%), making the air quite dry.")

    # Wind
    interpretations.append(f"The wind speed is {wind_speed} m/s.")
    if wind_gust > 15: 
        interpretations.append(f"There are strong wind gusts, up to {wind_gust} m/s.")
    elif wind_speed > 10:
        interpretations.append("The wind is quite strong.")
    else:
        interpretations.append("The wind is gentle and calm.")

    # Probability of Precipitation (POP)
    if pop > 0.7:
        interpretations.append(f"There is a very high probability of rain ({int(pop*100)}%).")
    elif pop > 0.4:
        interpretations.append(f"There is a moderate chance of rain ({int(pop*100)}%).")
    else:
        interpretations.append(f"The probability of rain is low ({int(pop*100)}%).")

    # Visibility and Cloudiness
    if visibility >= 10000:
        interpretations.append("Visibility is excellent at 10 km.")
    elif visibility < 5000:
        interpretations.append("Visibility is low, around {visibility} meters.")
    
    if clouds_all == 0:
        interpretations.append("The sky is clear with no clouds.")
    elif clouds_all > 75:
        interpretations.append(f"The sky is very cloudy ({clouds_all}%).")
    else:
        interpretations.append(f"Cloudiness is at a moderate level ({clouds_all}%).")
        
    # Main Weather Description
    interpretations.append(f"The main weather condition is '{weather_main}' with a description of '{weather_description}'.")

    return " ".join(interpretations)

def interpret_climate(climate_data: dict) -> str:
    """
    Interprets all climate data parameters into a descriptive text.
    
    Args:
        climate_data (dict): A dictionary containing all climate details.
        
    Returns:
        str: A comprehensive text interpretation of the climate conditions.
    """
    aqi = climate_data.get("aqi")
    co = climate_data.get("co")
    no = climate_data.get("no")
    no2 = climate_data.get("no2")
    o3 = climate_data.get("o3")
    so2 = climate_data.get("so2")
    pm2_5 = climate_data.get("pm2_5")
    pm10 = climate_data.get("pm10")
    nh3 = climate_data.get("nh3")

    interpretations = []

    # AQI
    if aqi == 1:
        interpretations.append(f"The Air Quality Index (AQI) is at a Good level ({aqi}). The air is fresh and healthy.")
    elif aqi == 2:
        interpretations.append(f"The Air Quality Index (AQI) is at a Fair level ({aqi}).")
    elif aqi == 3:
        interpretations.append(f"The Air Quality Index (AQI) is at a Moderate level ({aqi}).")
    elif aqi == 4:
        interpretations.append(f"The Air Quality Index (AQI) is at a Poor level ({aqi}).")
    elif aqi == 5:
        interpretations.append(f"The Air Quality Index (AQI) is at a Very Poor level ({aqi}).")
    
    # PM2.5
    if pm2_5 < 10:
        interpretations.append(f"The concentration of fine particulate matter PM2.5 is low at {pm2_5} μg/m3, which is very good for health.")
    elif 10 <= pm2_5 < 25:
        interpretations.append(f"The concentration of PM2.5 is at a fair level, at {pm2_5} μg/m3.")
    elif 25 <= pm2_5 < 50:
        interpretations.append(f"The concentration of PM2.5 is high, at {pm2_5} μg/m3.")
    elif 50 <= pm2_5 < 75:
        interpretations.append(f"The concentration of PM2.5 is at a poor level, at {pm2_5} μg/m3.")
    else:
        interpretations.append(f"The concentration of PM2.5 is at a very poor level, at {pm2_5} μg/m3.")

    # PM10
    if pm10 < 20:
        interpretations.append(f"The concentration of particulate matter PM10 is low at {pm10} μg/m3.")
    elif 20 <= pm10 < 50:
        interpretations.append(f"The concentration of PM10 is at a fair level, at {pm10} μg/m3.")
    elif 50 <= pm10 < 100:
        interpretations.append(f"The concentration of PM10 is at a moderate level, at {pm10} μg/m3.")
    elif 100 <= pm10 < 200:
        interpretations.append(f"The concentration of PM10 is at a poor level, at {pm10} μg/m3.")
    else:
        interpretations.append(f"The concentration of PM10 is at a very poor level, at {pm10} μg/m3.")

    # O3
    if o3 < 60:
        interpretations.append(f"The concentration of Ozone (O3) is at a good level, at {o3} μg/m3.")
    elif 60 <= o3 < 100:
        interpretations.append(f"The concentration of O3 is at a fair level, at {o3} μg/m3.")
    elif 100 <= o3 < 140:
        interpretations.append(f"The concentration of O3 is at a moderate level, at {o3} μg/m3.")
    elif 140 <= o3 < 180:
        interpretations.append(f"The concentration of O3 is at a poor level, at {o3} μg/m3.")
    else:
        interpretations.append(f"The concentration of O3 is at a very poor level, at {o3} μg/m3.")

    # Other pollutants
    if co < 4400:
        interpretations.append(f"The Carbon Monoxide (CO) concentration is at a good level, at {co} μg/m3.")
    elif 4400 <= co < 9400:
        interpretations.append(f"The CO concentration is at a fair level, at {co} μg/m3.")
    else:
        interpretations.append(f"The CO concentration is high, at {co} μg/m3.")
    
    if no2 < 40:
        interpretations.append(f"The Nitrogen Dioxide (NO2) concentration is at a good level, at {no2} μg/m3.")
    elif 40 <= no2 < 70:
        interpretations.append(f"The NO2 concentration is at a fair level, at {no2} μg/m3.")
    else:
        interpretations.append(f"The NO2 concentration is at a moderate level, at {no2} μg/m3.")
    
    if so2 < 20:
        interpretations.append(f"The Sulfur Dioxide (SO2) concentration is at a good level, at {so2} μg/m3.")
    elif 20 <= so2 < 80:
        interpretations.append(f"The SO2 concentration is at a fair level, at {so2} μg/m3.")
    else:
        interpretations.append(f"The SO2 concentration is high, at {so2} μg/m3.")
        
    if nh3 < 20:
        interpretations.append(f"The Ammonia (NH3) concentration is at a good level, at {nh3} μg/m3.")
    else:
        interpretations.append(f"The Ammonia (NH3) concentration is elevated, at {nh3} μg/m3.")

    return " ".join(interpretations)

def interpret_uv_index(uv_data: dict) -> str:
    """
    Interprets the UV index (UVI) into a descriptive text.
    
    Args:
        uv_data (dict): A dictionary containing the UV index.
        
    Returns:
        str: A text interpretation of the UV index.
    """
    uvi = uv_data.get("uvi")
    interpretations = []

    if uvi < 3:
        interpretations.append(f"The UV index is at a Low level ({uvi}). It is safe to be outdoors without protection.")
    elif uvi < 6:
        interpretations.append(f"The UV index is at a Moderate level ({uvi}). Protection is recommended when outdoors for extended periods.")
    elif uvi < 8:
        interpretations.append(f"The UV index is at a High level ({uvi}). You should cover up and use sunscreen when going outside.")
    elif uvi < 11:
        interpretations.append(f"The UV index is at a Very High level ({uvi}). It is best to limit time outdoors, especially around noon, and use full protection.")
    else:
        interpretations.append(f"The UV index is at an Extreme level ({uvi}). You must be extremely careful and avoid being in direct sunlight.")

    return " ".join(interpretations)


def interpret_daily_data_for_single_user_city(user_city_data: dict) -> list:
    """
    Interprets weather, climate, and UV data for each period of a single user-city pair,
    and returns a list of interpreted text strings.

    Args:
        user_city_data (dict): A dictionary representing a single user-city pair
                               with their daily data.

    Returns:
        list: A list containing a single string that combines all interpreted data
              for all periods.
    """
    interpreted_texts = []
    
    for period_data in user_city_data["daily_data"]:
        # Interpret each set of data
        weather_text = interpret_weather(period_data["weather_details"])
        climate_text = interpret_climate(period_data["climate_details"])
        uvi_text = interpret_uv_index(period_data["uvi_details"])
        
        # Combine interpretations into a single string
        full_interpretation = (
            f"During the {period_data['period']}, "
            f"the weather conditions are as follows: {weather_text} "
            f"The air quality is described as: {climate_text} "
            f"And the UV radiation is described as: {uvi_text}"
        )

        interpreted_texts.append(full_interpretation)
        
    return interpreted_texts