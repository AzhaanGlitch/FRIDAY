// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[tauri::command]
fn get_system_status() -> String {
    format!("FRIDAY Native Desktop Layer operational on {}", std::env::consts::OS)
}

fn main() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![get_system_status])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}

