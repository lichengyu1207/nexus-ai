"""
服务模块
"""
from .stats_service import (
    get_overview_stats,
    get_user_growth_stats,
    get_task_stats,
    get_system_health,
    get_activity_stats,
    export_stats_csv,
    stats_cache,
)
from .geocoder import (
    Geocoder,
    GeocodeResult,
    geocode_address,
    get_geocoder,
)
from .map_aggregator import (
    get_map_data,
    get_heatmap_data,
    get_location_summary,
    aggregate_by_province,
    aggregate_by_city,
    aggregate_by_district,
    get_point_data,
    get_new_locations,
    get_map_stats,
    clear_map_cache,
    clear_cache_by_prefix,
)
from .entity_recognition import (
    EntityRecognizer,
    ExtractedEntity,
    ParsedRequirement,
    parse_natural_language,
    entity_recognizer,
)
from .house_type_service import (
    get_area_estimate,
    get_all_house_types,
    add_house_type_stat,
    init_house_type_data,
    normalize_house_type,
    parse_house_type,
    DEFAULT_AREA_STATS,
    CITY_AREA_MULTIPLIERS,
)
from .price_estimator import (
    estimate_price,
    get_district_price,
    get_all_district_prices,
    add_district_price,
    init_district_price_data,
    get_city_average_price,
    DEFAULT_CITY_PRICES,
    HOUSE_TYPE_PRICE_ADJUSTMENTS,
    SPECIAL_REQUIREMENT_ADJUSTMENTS,
)
