reward_list = [
    {"id": 1, "nama_reward": "Badge Visual", "kategori": "simbolik",
        "vark_bonus": "visual", "ams_target": "intrinsic", "poin_dibutuhkan": 30},
    {"id": 2, "nama_reward": "Voucher Kecil", "kategori": "fungsional",
        "vark_bonus": "auditory", "ams_target": "extrinsic", "poin_dibutuhkan": 40},
    {"id": 3, "nama_reward": "Skin Karakter", "kategori": "kosmetik",
        "vark_bonus": "kinesthetic", "ams_target": "intrinsic", "poin_dibutuhkan": 50},
    {"id": 4, "nama_reward": "Ebook Gratis", "kategori": "fungsional",
        "vark_bonus": "reading", "ams_target": "amotivation", "poin_dibutuhkan": 25},
    {"id": 5, "nama_reward": "Sticker Eksklusif", "kategori": "simbolik",
        "vark_bonus": "visual", "ams_target": "extrinsic", "poin_dibutuhkan": 20},
    {"id": 6, "nama_reward": "Akses Premium", "kategori": "fungsional",
        "vark_bonus": "reading", "ams_target": "intrinsic", "poin_dibutuhkan": 45},
    {"id": 7, "nama_reward": "Skin Gerakan", "kategori": "kosmetik",
        "vark_bonus": "kinesthetic", "ams_target": "amotivation", "poin_dibutuhkan": 50},
    {"id": 8, "nama_reward": "Voucher Audio", "kategori": "fungsional",
        "vark_bonus": "auditory", "ams_target": "amotivation", "poin_dibutuhkan": 30},
    {"id": 9, "nama_reward": "Pin Koleksi", "kategori": "simbolik",
        "vark_bonus": "visual", "ams_target": "intrinsic", "poin_dibutuhkan": 22},
    {"id": 10, "nama_reward": "Akses Game", "kategori": "fungsional",
        "vark_bonus": "reading", "ams_target": "extrinsic", "poin_dibutuhkan": 55},
    # Tambahkan 25 lagi:
]

for i in range(11, 36):
    reward_list.append({
        "id": i,
        "nama_reward": f"Reward Tambahan {i}",
        "kategori": "simbolik" if i % 3 == 0 else "fungsional",
        "vark_bonus": "visual",
        "ams_target": "intrinsic",
        "poin_dibutuhkan": 20 + i
    })
