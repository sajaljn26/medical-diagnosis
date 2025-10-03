from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to AI-Medical!"}

@app.get("/health")
def health_check():
    return {"message": "OK"}


def main():
    print("Hello from ai-medical!")


if __name__ == "__main__":
    main()
