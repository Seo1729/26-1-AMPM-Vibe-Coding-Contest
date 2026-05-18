use pyo3::prelude::*;

fn haversine_distance(lat1: f64, lng1: f64, lat2: f64, lng2: f64) -> f64 {
    let r = 6371000.0; // 지구 반지름 (미터)
    let phi1 = lat1.to_radians();
    let phi2 = lat2.to_radians();
    let delta_phi = (lat2 - lat1).to_radians();
    let delta_lambda = (lng2 - lng1).to_radians();

    let a = (delta_phi / 2.0).sin().powi(2)
        + phi1.cos() * phi2.cos() * (delta_lambda / 2.0).sin().powi(2);
    let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());

    r * c
}

// 유저 위치 기준, 각 게시글이 허용 반경(radius_limit) 내에 있는지 검사하여 
// 노출 가능한 게시글 여부(1 또는 0)를 벡터로 반환 [cite: 28, 88]
#[pyfunction]
fn filter_local_posts(
    user_lat: f64,
    user_lng: f64,
    post_lats: Vec<f64>,
    post_lngs: Vec<f64>,
    radius_limits: Vec<f64>,
) -> PyResult<Vec<i32>> {
    let mut render_flags = Vec::new();

    for i in 0..post_lats.len() {
        let dist = haversine_distance(user_lat, user_lng, post_lats[i], post_lngs[i]);
        // 게시글 작성 시 설정한 오차 보정 범위(반경) 내에 있을 때만 노출 가능 [cite: 34, 88]
        if dist <= radius_limits[i] {
            render_flags.push(1); // 내 주변 게시글 노출 대상 
        } else {
            render_flags.push(0); // 너무 멀어서 제외
        }
    }

    Ok(render_flags)
}

#[pymodule]
fn geo_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(filter_local_posts, m)?)?;
    Ok(())
}