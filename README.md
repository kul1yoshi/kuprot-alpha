# KUProtect Alpha

This project is a tool for obfuscating Python code. It uses the `ast` module to transform the source code by changing variable names, function names, class names and string constants.

## Project structure

- ** `main.py`**: The main file containing the obfuscation logic.
- **`sources/in.py`**: Input file containing the source code to be obfuscated.
- **`sources/out.py`**: Output file with the obfuscated code.

## How to use

1. Place your source code in the `sources/in.py` file.
2. Run `main.py`:
 ```bash
 python main.py
 ```
3. The obfuscated code will be saved in `sources/out.py`.

## Dependencies

- Python 3.9 or higher.

## License

This project is distributed under the [MIT License](LICENSE).
