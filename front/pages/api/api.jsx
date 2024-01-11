import axios from "axios";

export const api = axios.create({
  baseURL: 'http://192.168.0.29:8000/api/',
  withCredentials: true,
  headers: {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVpZCI6IiQyYiQxMiRuMnJ1eUV5NjVUcjMySXRxLmRXdHJ1STJuV3VCdi5WTVpheUxqcWlMZkRleko1UWhwc0IzVyIsImV4cCI6MTcwNDg3MjczMH0.RSCAgp97v3UcEsoL9Jpe3lyiNaLreI8anINBLO822-M',
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json'
  },
});

export const getConnections = () => {
  return api.get('/connection/all')
    .then(response => response.data)
    .catch(error => console.log(error))
  ;
};
