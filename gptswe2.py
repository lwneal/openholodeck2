import json
import os
import subprocess
import sys
import os
import json
import openai
import argparse
import os
import re
from gptwc import token_count

CODE_BLOCK_LANGUAGES = ['python', 'js', 'javascript', 'c', 'cpp', 'java', 'bash', 'shell', 'sql', 'html', 'css', 'xml', 'json', 'yaml', 'yml', 'markdown', 'plaintext', 'md', 'txt', 'text', 'csv']

DEFAULT_TASK = """### 
### Write a task for the AI below
### Lines beginning with ### will be ignored
Please read all the attached code files, and carefully inspect them for any bugs or errors. If you find any obvious bugs or errors, fix them.
"""

openai.api_key = json.load(open(os.path.expanduser('~/.openai.json')))['api_key']


def chatgpt(input_text):
    messages = [
        {"role": "system", "content": "You are a highly advanced software engineering AI. Write complete source code files, but only output files that need to be changed."},
        {"role": "user", "content": input_text},
    ]
    client = openai.OpenAI(api_key=openai.api_key)
    response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.9,
            max_tokens=4095,
            n=1,
            stream=True,
    )
    chunks = []
    for chunk in response:
        if chunk.choices[0].delta.content is None:
            continue
        word = chunk.choices[0].delta.content
        print(word, end='')
        chunks.append(word)
    print()
    return ''.join(chunks)



def read_file_content(filepath, ignore_starting_with=None):
    with open(filepath, 'r') as file:
        if ignore_starting_with is None:
            return file.read()
        lines = file.readlines()
        return ''.join([line for line in lines if not line.startswith(ignore_starting_with)])


def extract_code_blocks(content):
    code_blocks = []
    code_block_pattern = re.compile(r'(?:(.*?)\n)?```(.*?)\n(.*?)```', re.DOTALL)
    
    matches = code_block_pattern.findall(content)
    for match in matches:
        filename = None
        preceding_content = match[0].strip()
        language_indicator = match[1]
        code = match[2]

        # Heuristics: Try to extract a filename

        # Handle cases like:
        #
        # # src/server.py
        # ```
        #
        # or
        #
        # # src/server.py
        # ```python
        if preceding_content:
            final_line = preceding_content.split('\n')[-1]
            potential_filename = final_line.split()[-1].strip('*').strip('`')
            if os.path.exists(potential_filename):
                filename = potential_filename

        # Handle the case:
        #
        # ```server.py
        if os.path.exists(language_indicator):
            filename = language_indicator

        if not filename:
            print("Failed to parse filename from block:")
            print(preceding_content)
            print(language_indicator)
            print(code)
            print("Could not find a filename for code block length {}".format(len(code)))
            continue
        code_blocks.append((filename, code))
        print("Writing code block length {} to file {}".format(len(code), filename))
    return code_blocks


def write_code_blocks(code_blocks):
    for filename, code in code_blocks:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as file:
            file.write(code)
    

def main():
    with open('gptswe.json', 'r') as config_file:
        config = json.load(config_file)

    prompt = []

    # Add intro text
    prompt.extend(config["intro_text"])

    # Add file contents
    for file_path in config["files"]:
        prompt.append(f'# {file_path}')
        prompt.append('```')
        if os.path.exists(file_path):
            prompt.append(read_file_content(file_path))
        else:
            prompt.append(f'File not found: {file_path}')
        prompt.append('```')
        prompt.append('')  # Add a newline for separation

    with open('gpt-task.txt', 'w') as task_file:
        task_file.write("### Context:")
        tokens_total = 0
        for file_path in config["files"]:
            tokens = token_count(read_file_content(file_path))
            task_file.write("### {} ({} tokens)\n".format(file_path, tokens))
            tokens_total += tokens
        task_file.write("### Total context tokens: {}\n".format(tokens_total))
        task_file.write(DEFAULT_TASK)

    # Open vim to edit ./task.txt
    editor = os.environ.get('EDITOR', 'vim')
    subprocess.run([editor, 'gpt-task.txt'])
    
    # Add task.txt
    prompt.append(read_file_content('./task.txt', "### "))

    # Add conclusion text
    prompt.extend(config["conclusion_text"])

    # Output the final prompt
    for line in prompt:
        print(line)

    # Save the result as `gpt-input.txt`
    with open('gpt-input.txt', 'w') as output_file:
        output_file.write('\n'.join(prompt))

    # Now call GPT to generate the response, and save the response as `gpt-output.txt`
    input_text = read_file_content('gpt-input.txt')
    output_text = chatgpt(input_text)
    with open('gpt-output.txt', 'w') as output_file:
        output_file.write(output_text)
    print("Saved output {} bytes to `gpt-output.txt`".format(len(output_text)))

    # Now parse the GPT output and write the code blocks to the corresponding files
    code_blocks = extract_code_blocks(output_text)
    write_code_blocks(code_blocks)


if __name__ == '__main__':
    main()
