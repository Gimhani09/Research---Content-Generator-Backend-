from generate_english import generate_english
from generate_sinhala import generate_sinhala
from generate_image import generate_poster

def create_ai_poster(prompt, language="si"):
    
    # --- Generate Text ---
    if language == "en":
        text = generate_english(prompt)
    elif language == "si":
        text = generate_sinhala(prompt + " සඳහා සිංහල ප්‍රචාරණ පණිවිඩයක් ලියන්න.")
    elif language == "both":
        en = generate_english(prompt)
        si = generate_sinhala("මෙම English පැහැදිලි කිරීම Sinhala වලට ගලපන්න: " + en)
        text = si + "\n\n" + en
    else:
        text = generate_english(prompt)

    # --- Generate Poster Image ---
    poster_prompt = f"""
    Create a Sri Lankan style marketing poster.
    Include the following text in Sinhala/English exactly:
    \"{text}\"
    Use clean professional layout.
    Add product image style graphics.
    """

    poster_path = generate_poster(poster_prompt)

    return text, poster_path


if __name__ == "__main__":
    t, p = create_ai_poster("introducing our new milk powder product", language="si")
    print("Generated Text:\n", t)
    print("Poster Saved At:", p)
