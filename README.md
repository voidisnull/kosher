# 🚀 Kosher - Effortless Dev Environments

Kosher is a comprehensive ⚡ CLI-based tool that empowers developers to effortlessly manage and reproduce their development environments. By encapsulating all necessary settings, including programming language versions, dependencies, and build instructions, Kosher ensures consistent and reliable development environments across different machines and teams. 💻

## 🌟 Why Use Kosher?
- 🗂 **Standardized Environment Management**: Define and manage all dependencies and settings in a single command-line interface.
- 🔁 **Effortless Reproducibility**: Recreate development environments with a single command.
- 🐳 **Seamless Docker Integration**: Ensures uniformity across different systems.
- 🌍 **Multi-Language Support**: Works with Python, Node.js, Ruby, and more.
- ⚡ **Lightweight and Efficient**: Minimal resource usage while maintaining high performance.
- 🚀 **Rapid Setup**: Get started with just a few commands.
- 🔄 **Version Control Integration**: Keep environment configuration alongside source code.

## 🛠️ Installation
Install Kosher quickly with a single command:
```sh
pip install kosher
```

## ⚡ Quick Start
1. 🏗 Create a new Kosher environment:
   ```sh
   kosher create <name> -l <language> -v <version> [-r <requirements>]
   ```
2. 🚀 Activate an existing environment:
   ```sh
   kosher activate <name>
   ```
3. 🏃 Run code inside the environment:
   ```sh
   kosher run <name> -c <code_file>
   ```
4. 🔨 Build source code inside the environment:
   ```sh
   kosher build <name> -s <source_dir> [-o <output_dir>]
   ```
5. 🛑 Delete an environment:
   ```sh
   kosher delete <name>
   ```
6. 📜 List all available environments:
   ```sh
   kosher list
   ```


## 🤝 Contributing
We ❤️ contributions from the community! If you have ideas, feature requests, or bug reports, feel free to submit issues and pull requests to help improve Kosher. 🚀

## 📜 License
Kosher is released under the MIT License. 📄

## 🌎 Stay Connected
For more information, updates, and to contribute, visit our [GitHub Repository](https://github.com/voidisnull/kosher). 🏆

