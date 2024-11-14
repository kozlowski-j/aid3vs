from openai import OpenAI, OpenAIError
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION_ID")

client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)


system_message = """
You are an expert Software Developer with excellent Python programming skills. 
You are also an expert in Typescript and you are very helpful. You will be given a long piece of Typescript code and you need to convert it to Python code.
Typescript code will be provided in the prompt. You need to convert it to Python code.
"""


def get_custom_response(prompt):
    try:
        chat_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            max_tokens=10000,  # Limit the response length
            temperature=0.7,  # Adjust creativity (0 = deterministic, 1 = creative)
        )
        return chat_response.choices[0].message.content
    except OpenAIError as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == '__main__':
    typescript_code = """
        import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";

export class OpenAIService {
  private openai: OpenAI;

  constructor() {
    this.openai = new OpenAI();
  }

  /**
   * Handles OpenAI API interactions for chat completions and embeddings.
   * Uses OpenAI's chat.completions and embeddings APIs.
   * Supports streaming, JSON mode, and different models.
   * Logs interactions to a prompt.md file for debugging.
   */
  async completion(
    messages: ChatCompletionMessageParam[],
    model: string = "gpt-4",
    stream: boolean = false,
    jsonMode: boolean = false
  ): Promise<OpenAI.Chat.Completions.ChatCompletion | AsyncIterable<OpenAI.Chat.Completions.ChatCompletionChunk>> {
    try {
      const chatCompletion = await this.openai.chat.completions.create({
        messages,
        model,
        stream,
        response_format: jsonMode ? { type: "json_object" } : { type: "text" }
      });

      if (stream) {
        return chatCompletion as AsyncIterable<OpenAI.Chat.Completions.ChatCompletionChunk>;
      } else {
        return chatCompletion as OpenAI.Chat.Completions.ChatCompletion;
      }
    } catch (error) {
      console.error("Error in OpenAI completion:", error);
      throw error;
    }
  }

  /**
   * Creates an embedding for the given input using OpenAI's text-embedding-3-large model.
   * @param input - A string or array of strings to create embeddings for.
   * @returns A Promise resolving to an array of numbers representing the embedding.
   * @throws Error if there's an issue creating the embedding.
   */
  async createEmbedding(input: string | string[]): Promise<number[]> {
    try {
      const embedding = await this.openai.embeddings.create({
        model: "text-embedding-3-large",
        input: input,
        encoding_format: "float",
      });

      // Return the embedding vector
      return embedding.data[0].embedding;
    } catch (error) {
      console.error("Error in creating embedding:", error);
      throw error;
    }
  }
}
        """

    prompt = "Convert below Typescript code to Python:\n\n" + typescript_code

    response = get_custom_response(prompt)
    print(response)
    file_name = "ts_to_python_response.md"
    with open(file_name, 'w') as file:
        file.write(response)