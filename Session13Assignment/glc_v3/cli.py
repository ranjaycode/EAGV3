import sys
import uvicorn


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        print("Starting glc_v3 Gateway Server on http://127.0.0.1:8111 ...")
        uvicorn.run("glc_v3.gateway:app", host="127.0.0.1", port=8111, reload=False)
    else:
        print("Usage: uv run glc serve")


if __name__ == "__main__":
    main()
