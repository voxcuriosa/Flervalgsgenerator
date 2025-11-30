from scrape_ndla import process_node, get_node_details
from storage import get_db_connection

def rescrape():
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return

    subjects = [
        ("Historie vg2", "urn:subject:1:ff69c291-6374-4766-80c2-47d5840d8bbf"),
        ("Historie vg3", "urn:subject:cc109c51-a083-413b-b497-7f80a0569a92"),
        ("Historie (PB)", "urn:subject:846a7552-ea6c-4174-89a4-85d6ba48c96e"),
        ("Sosiologi og sosialantropologi", "urn:subject:1:fb6ad516-0108-4059-acc3-3c5f13f49368")
    ]

    for name, urn in subjects:
        print(f"Rescraping {name}...")
        node_data = get_node_details(urn)
        if node_data:
            process_node(node_data, [], engine, name)
        else:
            print(f"Could not find node details for {name}")

if __name__ == "__main__":
    rescrape()
