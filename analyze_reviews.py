import pandas as pd
import re
from datetime import datetime, timedelta

def check_employee_mention(text):
    """
    Check if review mentions a specific employee by name or role.
    Returns True if employee is mentioned.
    """
    if pd.isna(text) or not isinstance(text, str):
        return False

    text_lower = text.lower()

    # Common employee roles/titles
    role_patterns = [
        r'\b(the\s+)?(mechanic|technician|tech|service\s+advisor|advisor|manager|owner|receptionist|staff\s+member)\b',
        r'\b(the\s+)?(front\s+desk|counter)\s+(guy|gal|woman|man|person|lady|gentleman)\b',
        r'\b(the\s+)?(guy|gal|woman|man|person|lady|gentleman)\s+(who|that|at)\b',
        r'\b(the\s+)?owner\b',
        r'\b(the\s+)?team\s+member\b',
        r'\bworked\s+with\s+\w+\b',
        r'\bhelped\s+(me|us)\b.*\b(he|she|they)\b',
        r'\b(he|she)\s+(was|is|did|explained|helped|fixed|took|went|stayed|made|kept|called|showed)\b',
        r'\b(his|her)\s+(work|service|attention|help|expertise|knowledge)\b',
    ]

    for pattern in role_patterns:
        if re.search(pattern, text_lower):
            return True

    # Check for proper names (capitalized words that might be names)
    # Common patterns: "John helped me", "Thanks Mike!", "Shout out to Sarah"
    name_patterns = [
        r'\b[A-Z][a-z]+\s+(helped|assisted|fixed|explained|took|was\s+great|was\s+amazing|was\s+awesome|was\s+fantastic|was\s+wonderful|did\s+a\s+great|is\s+the\s+best|went\s+above|stayed\s+late)\b',
        r'\b(thanks?\s+to|shout\s*out\s+to|kudos\s+to|props\s+to|ask\s+for|worked\s+with|helped\s+by|assisted\s+by|serviced\s+by|see|saw)\s+[A-Z][a-z]+\b',
        r'\b[A-Z][a-z]+\s+[A-Z]\.?\s',  # First name Last initial pattern
        r'\b[A-Z][a-z]+\s+(and|&)\s+[A-Z][a-z]+\b',  # Two names together
        r'\b(mr|mrs|ms|dr)\.?\s+[A-Z][a-z]+\b',
    ]

    for pattern in name_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Additional check: Look for attribution of actions to a person
    attribution_patterns = [
        r'\b(the\s+)?(person|individual|employee|worker|rep|representative)\s+(who|that)\b',
        r'\b(everyone|staff|crew|team)\s+(there|here|was|were|is|are)\b',
    ]

    for pattern in attribution_patterns:
        if re.search(pattern, text_lower):
            return True

    return False


def check_seasonal_work(text):
    """
    Check if review mentions seasonal timing/motivation for service.
    Returns True if seasonal work is mentioned.
    """
    if pd.isna(text) or not isinstance(text, str):
        return False

    text_lower = text.lower()

    # Seasonal keywords and patterns
    seasonal_patterns = [
        # Weather-related timing
        r'\b(before|ahead\s+of|for|getting\s+ready\s+for)\s+(the\s+)?(summer|winter|spring|fall|autumn)\b',
        r'\b(summer|winter|spring|fall|autumn)\s+(heat|cold|weather|season|driving|trip|months)\b',
        r'\b(hot|cold|warm|cool)\s+(weather|months|season)\b',
        r'\b(before|when)\s+(it\s+)?(gets|got)\s+(hot|cold|warm|cool)\b',
        r'\bfirst\s+(snow|freeze|frost|heat\s*wave)\b',
        r'\b(rainy|wet|dry|snow|icy)\s+season\b',

        # A/C and heating related seasonal
        r'\b(a/?c|air\s*conditioning|ac|heat|heater|heating)\s+(for|before|ready\s+for)\s+(summer|winter)\b',
        r'\b(summer|winter)\s+(a/?c|air\s*conditioning|ac|heat|heater)\b',
        r'\bready\s+for\s+(summer|winter)\b',

        # Trip/holiday related seasonal timing
        r'\b(before|ahead\s+of|for)\s+(a\s+)?(road\s+trip|trip|vacation|holiday|thanksgiving|christmas|memorial\s+day|labor\s+day|4th\s+of\s+july|july\s+4th)\b',
        r'\b(holiday|vacation|thanksgiving|christmas)\s+(travel|trip|driving|season)\b',

        # Tire/brake seasonal prep
        r'\b(winter|snow|all[- ]season)\s+(tires?|tyres?)\b',
        r'\btires?\s+(for|before)\s+(winter|snow|summer)\b',
        r'\b(brake|brakes)\s+(for|before)\s+(winter|snow)\b',

        # General seasonal prep language
        r'\bgetting\s+(the\s+)?(car|vehicle)\s+ready\s+for\b',
        r'\bseasonal\s+(maintenance|service|check|checkup|inspection)\b',
        r'\b(winterize|winterizing|winterization)\b',
        r'\b(spring|fall)\s+(tune[- ]?up|maintenance|service|check)\b',
    ]

    for pattern in seasonal_patterns:
        if re.search(pattern, text_lower):
            return True

    return False


def parse_relative_date(date_str):
    """
    Parse relative date strings like '2 months ago', 'a week ago' into estimated month.
    Returns the month number (1-12) or None if unparseable.
    """
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None

    today = datetime.now()
    date_lower = date_str.lower().replace('edited ', '')

    # Parse different formats
    if 'year' in date_lower:
        match = re.search(r'(\d+)\s+year', date_lower)
        years = int(match.group(1)) if match else 1
        estimated_date = today - timedelta(days=years * 365)
    elif 'month' in date_lower:
        match = re.search(r'(\d+)\s+month', date_lower)
        if match:
            months = int(match.group(1))
        elif 'a month' in date_lower:
            months = 1
        else:
            months = 1
        estimated_date = today - timedelta(days=months * 30)
    elif 'week' in date_lower:
        match = re.search(r'(\d+)\s+week', date_lower)
        if match:
            weeks = int(match.group(1))
        elif 'a week' in date_lower:
            weeks = 1
        else:
            weeks = 1
        estimated_date = today - timedelta(weeks=weeks)
    elif 'day' in date_lower:
        match = re.search(r'(\d+)\s+day', date_lower)
        if match:
            days = int(match.group(1))
        elif 'a day' in date_lower:
            days = 1
        else:
            days = 1
        estimated_date = today - timedelta(days=days)
    else:
        return None

    return estimated_date.month


def check_liberal_seasonal_work(text, date_str):
    """
    Liberal/relaxed check for seasonal work.
    Includes:
    - Everything from strict criteria
    - Any A/C or heating system work
    - Weather events (winter storm, freeze, heat wave)
    - Any mention of seasons
    - Road trips/vacations
    - Date-aware: heat issues in summer months, cold issues in winter months
    """
    if pd.isna(text) or not isinstance(text, str):
        return False

    text_lower = text.lower()

    # First check strict criteria
    if check_seasonal_work(text):
        return True

    # Liberal patterns - any mention of these topics
    liberal_patterns = [
        # Any A/C or heating work (assumes seasonal motivation)
        r'\b(a/?c|air\s*condition|ac\s|ac\.)\b',
        r'\b(heater|heating|heat\s+(issue|problem|not\s+working|stopped|broke|fix))\b',
        r'\b(fix|repair|replace|check|service)\w*\s+(the\s+)?(a/?c|ac|heat|heater)\b',

        # Weather events (even reactive)
        r'\b(winter|snow|ice|icy)\s*(storm|weather|conditions)\b',
        r'\b(storm|freeze|freezing|frozen|ice|icy|snow)\b',
        r'\bheat\s*wave\b',

        # Any season mention
        r'\b(winter|summer|spring|fall|autumn)\b',

        # Road trips and vacations (without requiring holiday)
        r'\b(road\s*trip|trip|vacation|travel|traveling|travelling)\b',

        # Temperature symptoms that suggest seasonal
        r'\b(overheating|overheat|running\s+hot|getting\s+hot|too\s+hot|no\s+heat|no\s+cold\s+air)\b',
        r'\b(coolant|radiator|cooling\s+system|thermostat)\b',
    ]

    for pattern in liberal_patterns:
        if re.search(pattern, text_lower):
            return True

    # Date-aware checks for ambiguous temperature mentions
    month = parse_relative_date(date_str)
    if month:
        summer_months = [6, 7, 8]  # June, July, August
        winter_months = [12, 1, 2]  # December, January, February

        # Hot/cooling issues in summer
        if month in summer_months:
            summer_patterns = [
                r'\b(hot|heat|warm)\b',
                r'\b(cool|cold|cooling)\b',  # wanting to cool down
            ]
            for pattern in summer_patterns:
                if re.search(pattern, text_lower):
                    return True

        # Cold/heating issues in winter
        if month in winter_months:
            winter_patterns = [
                r'\b(cold|freezing|frozen)\b',
                r'\b(heat|warm|warming)\b',  # wanting to warm up
            ]
            for pattern in winter_patterns:
                if re.search(pattern, text_lower):
                    return True

    return False


def process_file(input_path, output_path):
    """Process a single Excel file and add analysis columns."""
    print(f"Processing: {input_path}")

    df = pd.read_excel(input_path)

    # Add new columns
    df['employee_mention'] = df['content'].apply(check_employee_mention)
    df['seasonal_work'] = df['content'].apply(check_seasonal_work)
    df['liberal_seasonal_work'] = df.apply(
        lambda row: check_liberal_seasonal_work(row['content'], row['date']), axis=1
    )
    df['owner_response_present'] = df['owner_response'].astype(bool)

    # Save to new file
    df.to_excel(output_path, index=False)

    # Print summary
    emp_count = df['employee_mention'].sum()
    seasonal_count = df['seasonal_work'].sum()
    liberal_seasonal_count = df['liberal_seasonal_work'].sum()
    owner_resp_count = df['owner_response_present'].sum()
    total = len(df)
    print(f"  Total reviews: {total}")
    print(f"  Employee mentions: {emp_count} ({100*emp_count/total:.1f}%)")
    print(f"  Seasonal work (strict): {seasonal_count} ({100*seasonal_count/total:.1f}%)")
    print(f"  Seasonal work (liberal): {liberal_seasonal_count} ({100*liberal_seasonal_count/total:.1f}%)")
    print(f"  Owner responses: {owner_resp_count} ({100*owner_resp_count/total:.1f}%)")
    print(f"  Saved to: {output_path}")
    print()


def main():
    files = [
        ('Marietta_Auto_Repair_reviews_2026-02-25-19-58.xlsx',
         'Marietta_Auto_Repair_reviews_analyzed.xlsx'),
        ('Anthem Automotive reviews_2026-02-25-19-09.xlsx',
         'Anthem_Automotive_reviews_analyzed.xlsx'),
        ('Accurate Care Automotive - reviews_2026-02-22-22-27.xlsx',
         'Accurate_Care_Automotive_reviews_analyzed.xlsx'),
        ('Automotive Services reviews_2026-02-22-22-29.xlsx',
         'Automotive_Services_reviews_analyzed.xlsx'),
    ]

    for input_file, output_file in files:
        process_file(input_file, output_file)

    print("All files processed!")


if __name__ == "__main__":
    main()
