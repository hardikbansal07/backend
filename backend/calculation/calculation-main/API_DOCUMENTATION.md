# PyJHora API Documentation

This document details the comprehensive set of Vedic Astrology calculation endpoints available in the PyJHora API.

## Base URL
All endpoints are prefixed with `/api`.

## 1. Chart Calculations & Analysis

These endpoints provide detailed analysis of the horoscope chart.

*   **`GET /api/chart/analysis`**
    *   **Description**: Comprehensive chart analysis including Retrograde planets, Combust planets, Benefics/Malefics, Chara Karakas, Marakas, Argala, Virodhargala, Drishti (Graha & Rasi), and Special Lords (Rudra, Brahma, Maheshwara).
    *   **Params**: `request_id` (required), `divisional_chart_factor` (default: 1).

*   **`GET /api/chart/varnada`**
    *   **Description**: Calculates Varnada Lagna.
    *   **Params**: `request_id` (required), `divisional_chart_factor` (default: 1).

*   **`GET /api/chart/arudha`**
    *   **Description**: Calculates Bhava Arudhas, Surya Arudhas, Chandra Arudhas, and Graha Arudhas.
    *   **Params**: `request_id` (required), `divisional_chart_factor` (default: 1).

*   **`GET /api/chart/vaiseshikamsa`**
    *   **Description**: Calculates Vaiseshikamsa counts (Dhasavarga, Shadvarga, Sapthavarga, Shodhasavarga) and Vimsopaka Balas.
    *   **Params**: `request_id` (required).

*   **`GET /api/chart/sphuta`**
    *   **Description**: Calculates various Sphutas: Tri, Chatur, Pancha, Prana, Deha, Mrityu, Sookshma, Beeja, Kshetra, Tithi, Yoga, Yogi, Avayogi, Rahu Tithi.
    *   **Params**: `request_id` (required), `divisional_chart_factor` (default: 1).

*   **`GET /api/chart/strength`**
    *   **Description**: Calculates Planetary Strengths: Shadbala, Bhava Bala, Harsha Bala, Pancha Vargeeya Bala, Dwadhasa Vargeeya Bala, Ishta Phala, Subha Rashmi, Cheshta Rashmi.
    *   **Params**: `request_id` (required).

*   **`GET /api/chart/ashtakavarga`**
    *   **Description**: Calculates Ashtakavarga points (Binna, Samudhaya, Prastara) and Sodhaya Pindas.
    *   **Params**: `request_id` (required), `divisional_chart_factor` (default: 1).

*   **`GET /api/chart/dosha`**
    *   **Description**: Checks for various Doshas (Manglik, Kala Sarpa, Pitru, etc.).
    *   **Params**: `request_id` (required), `divisional_chart_factor` (default: 1), `language` (default: 'en').

*   **`GET /api/chart/yoga`**
    *   **Description**: Checks for general Yogas (e.g., Pancha Mahapurusha).
    *   **Params**: `request_id` (required), `divisional_chart_factor` (default: 1), `language` (default: 'en').

*   **`GET /api/chart/raja_yoga`**
    *   **Description**: Checks for Raja Yogas.
    *   **Params**: `request_id` (required), `divisional_chart_factor` (default: 1), `language` (default: 'en').

## 2. Dhasa Systems

Extensive support for various planetary and sign-based dhasa systems.

### Graha Dhasas (Planetary)
*   **`GET /api/dhasa/ashtottari`**: Ashtottari Dhasa.
*   **`GET /api/dhasa/yogini`**: Yogini Dhasa.
*   **`GET /api/dhasa/shodasottari`**: Shodasottari Dhasa.
*   **`GET /api/dhasa/dwadasottari`**: Dwadasottari Dhasa.
*   **`GET /api/dhasa/kaala`**: Kaala Dhasa.
    *   **Params**: `request_id`, `years`, `months`, `sixty_hours`, `include_antardhasa`.

### Rasi Dhasas (Sign-based)
*   **`GET /api/dhasa/chara`**: Jaimini Chara Dhasa.
*   **`GET /api/dhasa/kendraadhi_rasi`**: Kendraadhi Rasi Dhasa.
*   **`GET /api/dhasa/narayana`**: Narayana Dhasa.
*   **`GET /api/dhasa/sudasa`**: Sudasa Dhasa.
*   **`GET /api/dhasa/nirayana`**: Nirayana Shoola Dhasa.
*   **`GET /api/dhasa/shoola`**: Shoola Dhasa.
*   **`GET /api/dhasa/kalachakra`**: Kalachakra Dhasa.
*   **`GET /api/dhasa/drig`**: Drig Dhasa.
*   **`GET /api/dhasa/moola`**: Moola Dhasa.
*   **`GET /api/dhasa/brahma`**: Brahma Dhasa.
*   **`GET /api/dhasa/lagnamsaka`**: Lagnamsaka Dhasa.
*   **`GET /api/dhasa/mandooka`**: Mandooka Dhasa.
*   **`GET /api/dhasa/padhanadhamsa`**: Padhanadhamsa Dhasa.
*   **`GET /api/dhasa/paryaaya`**: Paryaaya Dhasa.
*   **`GET /api/dhasa/sandhya`**: Sandhya Dhasa.
*   **`GET /api/dhasa/sthira`**: Sthira Dhasa.
*   **`GET /api/dhasa/tara_lagna`**: Tara Lagna Dhasa.
*   **`GET /api/dhasa/trikona`**: Trikona Dhasa.
*   **`GET /api/dhasa/chakra`**: Chakra Dhasa.
*   **`GET /api/dhasa/sudharsana_chakra`**: Sudharsana Chakra Dhasa.

### Annual Dhasas
*   **`GET /api/dhasa/annual/mudda`**: Mudda Dhasa (Varsha Vimsottari).
*   **`GET /api/dhasa/annual/patyayini`**: Patyayini Dhasa.
*   **`GET /api/dhasa/annual/varsha_narayana`**: Varsha Narayana Dhasa.

**Common Params for Dhasas**: `request_id` (required), `limit` (default: 120), `include_antardhasa` (default: True), `divisional` (default: 1).

## 3. Transit & Tajaka (Annual Charts)

*   **`GET /api/transit/tajaka/annual`**
    *   **Description**: Calculates the Annual Chart (Varsha Pravesh).
    *   **Params**: `request_id`, `years` (age), `divisional_chart_factor`.

*   **`GET /api/transit/tajaka/monthly`**
    *   **Description**: Calculates the Monthly Chart (Maasa Pravesh).
    *   **Params**: `request_id`, `years`, `months`, `divisional_chart_factor`.

*   **`GET /api/transit/tajaka/sixty_hour`**
    *   **Description**: Calculates the 60-Hour Chart.
    *   **Params**: `request_id`, `years`, `months`, `sixty_hour_count`.

*   **`GET /api/transit/tajaka/lord_of_year`**
    *   **Description**: Determines the Lord of the Year (Varsheshwara).
    *   **Params**: `request_id`, `years`.

*   **`GET /api/transit/tajaka/lord_of_month`**
    *   **Description**: Determines the Lord of the Month (Maaseshwara).
    *   **Params**: `request_id`, `years`, `months`.

*   **`GET /api/transit/tajaka/yogas`**
    *   **Description**: Checks for Tajaka Yogas (Ishkavala, Induvara, Ithasala, Eesarpha, Nakta, Yamaya, Manahoo, Kamboola, Radda, Duhphali Kutta).
    *   **Params**: `request_id`, `years`, `divisional_chart_factor`.

*   **`GET /api/transit/saham`**
    *   **Description**: Calculates all Sahams (Punya, Vidya, Yasas, etc.).
    *   **Params**: `request_id`, `night_time_birth` (bool).

## 4. Panchanga & Prediction

*   **`GET /api/panchanga/pancha_paksha`**
    *   **Description**: Calculates Pancha Paksha (Bird Biorhythm) details.
    *   **Params**: `request_id`.

*   **`GET /api/panchanga/tithi_pravesha`**
    *   **Description**: Calculates Tithi Pravesha date.
    *   **Params**: `request_id`, `year`.

*   **`GET /api/prediction/general`**
    *   **Description**: General predictions based on Lagna/Rasi and planets in houses.
    *   **Params**: `request_id`, `language`.

*   **`GET /api/prediction/longevity`**
    *   **Description**: Longevity prediction (Alpayu, Madhyayu, Poornayu).
    *   **Params**: `request_id`.

*   **`GET /api/prediction/naadi_marriage`**
    *   **Description**: Checks Naadi Marriage Yogas.
    *   **Params**: `request_id`, `gender` (0=Male, 1=Female).

## 5. Matching

*   **`GET /api/match/compatibility`**
    *   **Description**: Calculates Ashtakoota compatibility score.
    *   **Params**: `boy_nakshatra`, `boy_pada`, `girl_nakshatra`, `girl_pada`, `method`.
