using System;
using System.Collections;
using System.Net.Sockets;
using System.Text;
using TMPro;
using UnityEngine;

/// <summary>
/// Отправляемая дата на сервер для регистрации
/// </summary>
[Serializable]
public class RequestJsonData {
    public ServerRequestCodes code = ServerRequestCodes.Registration;
    public string Email;
    public string Username;
    public string Password;
}

public class RegisterController : MonoBehaviour {

    [SerializeField] private TMP_InputField EmailInput;
    [SerializeField] private TMP_InputField UsernameInput;
    [SerializeField] private TMP_InputField PasswordInput;
    [SerializeField] private TMP_Text RegisterErrorText;
    [SerializeField] private GameObject LoadingScreen;

    private string serverIP = "89.189.179.132";
    private int serverPort = 53144;

    private Socket socket;

    private float connectTimeout = 15f;

    public void Register() {
        Debug.Log(EmailInput.text);
        Debug.Log(UsernameInput.text);
        Debug.Log(PasswordInput.text);

        // Преобразование в JSON
        RequestJsonData data = new RequestJsonData { Email = EmailInput.text, Username = UsernameInput.text, Password = PasswordInput.text };
        string jsonData = JsonUtility.ToJson(data);

        Debug.Log(jsonData);

        StartConnect(jsonData);
    }

    private void StartConnect(string jsonData) {
        StartCoroutine(ConnectToServerCoroutine(jsonData));
    }

    /// <summary>
    /// Подключение к серверу и отправка данных
    /// </summary>
    /// <param name="jsonData"></param>
    /// <returns></returns>
    private IEnumerator ConnectToServerCoroutine(string jsonData) {
        LoadingScreen.SetActive(true);
        RegisterErrorText.text = "";

        socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        IAsyncResult result = socket.BeginConnect(serverIP, serverPort, null, null);

        float timer = 0f;
        bool success = false;

        while (timer < connectTimeout) {
            if (result.IsCompleted) {
                success = true;
                break;
            }
            timer += Time.deltaTime;
            yield return null;
        }

        if (!success) {
            socket.Close();
            RegisterErrorText.text = "Error: Server connection timeout.";
            Debug.LogError("Timeout connecting to server.");
        } else {
            try {
                socket.EndConnect(result);
                Debug.Log("Connected to server.");

                try {
                    byte[] data = System.Text.Encoding.UTF8.GetBytes(jsonData);
                    socket.Send(data);
                    Debug.Log("Data sent to server.");
                    StartCoroutine(RecieveDataCoroutine());
                } catch (SocketException e) {
                    RegisterErrorText.text = "Connection error: " + e.Message;
                    Debug.LogError("Failed to send data to server: " + e.Message);
                }

            } catch (SocketException e) {
                RegisterErrorText.text = "Connection error: " + e.Message;
                Debug.LogError("Failed to connect to server: " + e.Message);
            }
        }

        LoadingScreen.SetActive(false);
    }

    private IEnumerator RecieveDataCoroutine() {
        byte[] buffer = new byte[1024];
        int bytesReceived = 0;

        IAsyncResult result = socket.BeginReceive(buffer, 0, buffer.Length, SocketFlags.None, null, null);

        float timer = 0f;
        bool success = false;

        while (timer < connectTimeout) {
            if (result.IsCompleted) {
                success = true;
                break;
            }
            timer += Time.deltaTime;
            yield return null;
        }

        if (!success) {
            socket.Close();
            RegisterErrorText.text = "Error: Data receive from server timeout.";
            Debug.LogError("Timeout receive data from server.");
        } else {
            try {
                bytesReceived = socket.EndReceive(result);
                if (bytesReceived == 0) {
                    socket.Close();
                    RegisterErrorText.text = "Error: None data receive from server.";
                    Debug.LogError("None data receive from server.");
                }

                string data = Encoding.UTF8.GetString(buffer, 0, bytesReceived);
                Debug.Log("Data received from server: " + data);

            } catch (SocketException e) {
                RegisterErrorText.text = "Connection error: " + e.Message;
                Debug.LogError("Failed to receive data from server: " + e.Message);
            }
        }

        LoadingScreen.SetActive(false);
    }
}

