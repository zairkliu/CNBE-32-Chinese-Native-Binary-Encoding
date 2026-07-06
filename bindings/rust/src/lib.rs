pub fn cnbe_encode(radix: u8, stroke: u8, structure: u8) -> u32 {
    (radix as u32) << 24 | (stroke as u32) << 19 | (structure as u32) << 15
}
pub fn cnbe_decode(code: u32) -> (u32, u32, u32) {
    ((code>>24)&0xFF, (code>>19)&0x1F, (code>>15)&0xF)
}
pub fn cnhe_cmp(a: u32, b: u32) -> u32 {
    let (ra,sa,ta)=cnbe_decode(a); let (rb,sb,tb)=cnbe_decode(b);
    (ra.max(rb)-ra.min(rb))*8+(sa.max(sb)-sa.min(sb))*5+(ta.max(tb)-ta.min(tb))*4
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn test_enc() { assert_eq!(cnbe_decode(cnbe_encode(1,1,0)),(1,1,0)); }
    #[test] fn test_cmp() { assert_eq!(cnhe_cmp(cnbe_encode(1,1,0),cnbe_encode(2,1,0)),8); }
}
