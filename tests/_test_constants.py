# sample data for w2 processing
sample_w2_success_response = """
{
    "employee_info": {
        "ssn": "123-45-6789",
        "name": "Abby L Smith",
        "address": "123 Sample Road",
        "city": "Columbus",
        "state": "OH",
        "zipcode": "43218"
    },
    "employer_info": {
        "ein": "12-1234567",
        "name": "Company ABC",
        "address": "444 Example Road",
        "city": "Columbus",
        "state": "OH",
        "zipcode": "43218"
    },
    "income_summary": {
        "wages_tips_other_compensation": "50000.00",
        "social_security_wages": "50000.00",
        "medicare_wages_tips": "50000.00",
        "social_security_tips": null,
        "allocated_tips": null,
        "dependent_care_benefits": null,
        "nonqualified_plans": null
    },
    "withholding_summary": {
        "federal_income_tax_withheld": "4092.00",
        "social_security_tax_withheld": "3100.00",
        "medicare_tax_withheld": "725.00"
    },
    "other_details": {
        "box_12a": {
            "code": null,
            "amount": null
        },
        "box_12b": {
            "code": null,
            "amount": null
        },
        "box_12c": {
            "code": null,
            "amount": null
        },
        "box_12d": {
            "code": null,
            "amount": null
        },
        "statutory_employee": false,
        "retirement_plan": false,
        "third_party_sick_pay": false,
        "box_14_other": null
    },
    "total_summary": [
        {
            "state": {
                "name": "OH",
                "state_eid": "12-3456789",
                "wages_tips": "50000.00",
                "tax": "1040.88"
            },
            "local": {
                "name": "Columbus",
                "wages_tips": "50000.00",
                "tax": "1250.00"
            }
        }
    ],
    "insights": [
        "Employee and Employer addresses are both in Columbus, OH, indicating single-state and single-locality employment and taxation.",
        "The Social Security tax withheld ($3,100.00) is 6.2% of Social Security wages ($50,000.00), which is correct for 2024.",
        "The Medicare tax withheld ($725.00) is 1.45% of Medicare wages and tips ($50,000.00), which is correct for 2024.",
        "Social Security wages of $50,000.00 are well below the 2024 Social Security wage cap of $168,600.",
        "The total taxable income reported is $50,000.00 (Box 1).",
        "State-wise, the employee earned $50,000.00 in Ohio wages and had $1,040.88 withheld for Ohio state income tax.",
        "Locality-wise, the employee earned $50,000.00 in Columbus local wages and had $1,250.00 withheld for Columbus local income tax.",
        "This employee earned $50,000.00, paid $4,092.00 in Federal income tax, $3,100.00 in Social Security tax, $725.00 in Medicare tax, $1,040.88 in State income tax, and $1,250.00 in Local income tax. There are no additional deductions or benefits reported in Boxes 12, 13, or 14."
    ],
    "model_assessment": {
        "average_confidence": 0.99,
        "warnings": [],
        "missing_fields": ["BOX 12D"],
        "overall_quality": "High"
    }
}
"""

sample_w2_error_response = """
{
    "error": {
        "message": "The provided W-2 forms are empty and do not contain any filled-in data for extraction."
    }
}
"""

# sample data for movies API
sample_movie_search_response = [
    {
        "Search": [
            {
                "Title": "Spider-Man: No Way Home",
                "imdbID": "tt10872600",
            },
            {
                "Title": "Spider-Man",
                "imdbID": "tt0145487",
            },
            {
                "Title": "Spider-Man: Homecoming",
                "imdbID": "tt2250912",
            },
            {
                "Title": "Spider-Man 2",
                "imdbID": "tt0316654",
            },
            {
                "Title": "Spider-Man: Into the Spider-Verse",
                "imdbID": "tt4633694",
            },
            {
                "Title": "The Amazing Spider-Man",
                "imdbID": "tt0948470",
            },
            {
                "Title": "Spider-Man 3",
                "imdbID": "tt0413300",
            },
            {
                "Title": "Spider-Man: Far from Home",
                "imdbID": "tt6320628",
            },
            {
                "Title": "The Amazing Spider-Man 2",
                "imdbID": "tt1872181",
            },
            {
                "Title": "Spider-Man: Across the Spider-Verse",
                "imdbID": "tt9362722",
            },
        ],
        "totalResults": "20",
        "Response": "True",
    },
    {
        "Search": [
            {
                "Title": "Spider-Man: Lotus",
                "imdbID": "tt13904644",
            },
            {
                "Title": "Spider-Plant Man",
                "imdbID": "tt0460946",
            },
            {
                "Title": "Jack Black: Spider-Man",
                "imdbID": "tt0331527",
            },
            {
                "Title": "Spider-Man: The Dragon's Challenge",
                "imdbID": "tt0077328",
            },
            {
                "Title": "Vjeran Tomic: The Spider-Man of Paris",
                "imdbID": "tt29274601",
            },
            {
                "Title": "Spider-Man: Homecoming, NBA Finals: Watch the Game",
                "imdbID": "tt7006122",
            },
            {
                "Title": "Spider-Man Strikes Back",
                "imdbID": "tt0078308",
            },
            {
                "Title": "The Amazing Adventures of Spider-Man",
                "imdbID": "tt0211194",
            },
            {
                "Title": "Spider Man: Lost Cause",
                "imdbID": "tt2803854",
            },
            {
                "Title": "Lego Marvel Spider-Man: Vexed by Venom",
                "imdbID": "tt10755644",
            },
        ],
        "totalResults": "20",
        "Response": "True",
    },
]

sample_movie_search_error_response = {"Response": "False", "Error": "Movie not found!"}

sample_movie_director_fetch_response = [
    {
        "Title": "Spider-Man: No Way Home",
        "Director": "Jon Watts",
        "imdbID": "tt10872600",
    },
    {
        "Title": "Spider-Man",
        "Director": "Jon",
        "imdbID": "tt0145487",
    },
    {
        "Title": "Spider-Man: Homecoming",
        "Director": "Watts",
        "imdbID": "tt2250912",
    },
    {
        "Title": "Spider-Man 2",
        "Director": "Jhon Wick",
        "imdbID": "tt0316654",
    },
    {
        "Title": "Spider-Man: Into the Spider-Verse",
        "Director": "Jon Snow",
        "imdbID": "tt4633694",
    },
    {
        "Title": "The Amazing Spider-Man",
        "Director": "Mathew",
        "imdbID": "tt0948470",
    },
    {
        "Title": "Spider-Man 3",
        "Director": "Thomas",
        "imdbID": "tt0413300",
    },
    {
        "Title": "Spider-Man: Far from Home",
        "Director": "Dan",
        "imdbID": "tt6320628",
    },
    {
        "Title": "The Amazing Spider-Man 2",
        "Director": "N/A",
        "imdbID": "tt1872181",
    },
]
