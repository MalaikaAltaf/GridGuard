import numpy as np
from scipy.stats import linregress
from typing import List, Dict, Any

def build_sgcc_monthly_features(monthly_usage_history: List[Dict[str, Any]], feature_names: List[str]) -> np.ndarray:
    """
    Builds the 39-feature vector for the SGCC monthly model.
    It expects a rolling history of exactly 34 months.
    """
    if len(monthly_usage_history) < 34:
        raise ValueError(f"SGCC model requires at least 34 months of history, got {len(monthly_usage_history)}")
    
    # We only take the latest 34 months if there are more
    history = monthly_usage_history[-34:]
    usages = [item["usage_kwh"] for item in history]
    
    # 1. month_001 to month_034 (latest 34 months)
    # The oldest of the 34 is month_001, latest is month_034.
    features_dict = {}
    for i, usage in enumerate(usages):
        features_dict[f"month_{i+1:03d}"] = usage
        
    # Engineered features
    usages_np = np.array(usages)
    
    # 2. mean_monthly_usage
    features_dict["mean_monthly_usage"] = np.mean(usages_np)
    
    # 3. std_monthly_usage
    features_dict["std_monthly_usage"] = np.std(usages_np)
    
    # 4. consumption_drop_pct
    # Compare recent average to historical average
    recent_3_months_avg = np.mean(usages_np[-3:])
    historical_avg = np.mean(usages_np[:-3]) if len(usages_np) > 3 else recent_3_months_avg
    if historical_avg > 0:
        drop = ((historical_avg - recent_3_months_avg) / historical_avg) * 100
        features_dict["consumption_drop_pct"] = max(0, drop)  # Only capture drops
    else:
        features_dict["consumption_drop_pct"] = 0.0
        
    # 5. trend_slope
    x = np.arange(len(usages_np))
    slope, _, _, _, _ = linregress(x, usages_np)
    features_dict["trend_slope"] = slope
    
    # 6. summer_winter_seasonal_ratio
    # This requires knowing the actual months to determine summer/winter.
    # For now, we will do a simple approximation if we don't have month labels mapped,
    # but the history has 'month' in YYYY-MM format.
    summer_months = ['05', '06', '07', '08', '09', '10']
    winter_months = ['11', '12', '01', '02', '03', '04']
    
    summer_usage = []
    winter_usage = []
    
    for item in history:
        month_str = item["month"].split("-")[1]
        if month_str in summer_months:
            summer_usage.append(item["usage_kwh"])
        elif month_str in winter_months:
            winter_usage.append(item["usage_kwh"])
            
    avg_summer = np.mean(summer_usage) if summer_usage else 1.0
    avg_winter = np.mean(winter_usage) if winter_usage else 1.0
    # Avoid division by zero
    if avg_winter == 0:
        avg_winter = 1.0
        
    features_dict["summer_winter_seasonal_ratio"] = avg_summer / avg_winter
    
    # Create the final ordered feature array based on feature_names
    final_features = []
    for name in feature_names:
        final_features.append(features_dict.get(name, 0.0))
        
    return np.array(final_features, dtype=float)


def format_precon_ami_features(hourly_usage_kwh: List[float], feature_names: List[str]) -> np.ndarray:
    """
    Format the 24 hourly readings for the PRECON AMI model.
    """
    if len(hourly_usage_kwh) != 24:
        raise ValueError("AMI model requires exactly 24 hourly readings")
        
    # The PRECON model might have feature names like 'hour_00' to 'hour_23' or similar.
    # If feature_names is just the 24 hours, we return the array directly.
    return np.array(hourly_usage_kwh, dtype=float)
