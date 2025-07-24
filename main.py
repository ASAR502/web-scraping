import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "controller:app",  # This tells uvicorn to look for 'app' inside 'controller.py'
        host="0.0.0.0",
        port=8000,
        reload=True
    )
