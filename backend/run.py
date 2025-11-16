from app import create_app

app = create_app()


print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule} -> endpoint={rule.endpoint} methods={list(rule.methods)}")

if __name__ == "__main__":
    app.run(debug=True)

