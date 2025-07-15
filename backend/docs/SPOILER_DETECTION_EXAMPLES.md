# Ví dụ Review theo Độ Tin Cậy Spoiler Detection

## Độ Tin Cậy Cao (> 80%) - Tự động đánh dấu spoiler

### 1. Tiết lộ kết thúc phim

```
"Kết thúc phim thật bất ngờ khi nhân vật chính hóa ra là kẻ phản bội và bị giết chết trong cảnh cuối.
Cảnh twist này làm tôi shock hoàn toàn vì không ai ngờ được sự thật đau lòng này."
```

**Từ khóa phát hiện:** `kết thúc`, `bất ngờ`, `hóa ra`, `kẻ phản bội`, `bị giết chết`, `cảnh cuối`, `twist`, `shock`, `sự thật đau lòng`
**Độ tin cậy:** ~95%

### 2. Tiết lộ cái chết nhân vật

```
"Phim có twist lớn khi nhân vật chính bị giết chết ở giữa phim.
Cái chết của anh ấy thật đau lòng và làm thay đổi hoàn toàn cốt truyện.
Sau đó mới biết hóa ra anh ta là người phản bội."
```

**Từ khóa phát hiện:** `twist`, `bị giết chết`, `cái chết`, `hóa ra`, `phản bội`
**Độ tin cậy:** ~90%

### 3. Tiết lộ thân phận bí mật

```
"SPOILER ALERT: Hóa ra nhân vật chính có thân phận bí mật - anh ta là con trai của kẻ thù chính.
Sự thật này được tiết lộ ở cuối phim và làm tôi shock hoàn toàn."
```

**Từ khóa phát hiện:** `spoiler alert`, `hóa ra`, `thân phận bí mật`, `kẻ thù chính`, `sự thật`, `tiết lộ`, `cuối phim`, `shock`
**Độ tin cậy:** ~98%

### 4. Tiết lộ twist ending

```
"Kết thúc phim có twist bất ngờ khi hóa ra tất cả chỉ là ảo giác của nhân vật chính.
Anh ta thực ra đã chết từ đầu phim và những gì xảy ra sau đó chỉ là tưởng tượng."
```

**Từ khóa phát hiện:** `kết thúc`, `twist bất ngờ`, `hóa ra`, `ảo giác`, `đã chết`, `tưởng tượng`
**Độ tin cậy:** ~92%

### 5. Tiết lộ quan hệ tình cảm

```
"Phim có twist về tình cảm khi hóa ra hai nhân vật chính là anh em ruột nhưng lại yêu nhau.
Khi biết sự thật này, họ đã chia tay vĩnh viễn và không bao giờ gặp lại."
```

**Từ khóa phát hiện:** `twist`, `hóa ra`, `anh em ruột`, `yêu nhau`, `sự thật`, `chia tay vĩnh viễn`
**Độ tin cậy:** ~88%

---

## Độ Tin Cậy Trung Bình (60-80%) - Cần kiểm tra thủ công

### 1. Nói về nhân vật chính

```
"Nhân vật chính trong phim có diễn biến tâm lý rất phức tạp.
Anh ta phải đối mặt với nhiều thử thách và cuối cùng đã thành công trong nhiệm vụ quan trọng."
```

**Từ khóa phát hiện:** `nhân vật chính`, `diễn biến`, `thử thách`, `thành công`, `nhiệm vụ quan trọng`
**Độ tin cậy:** ~65%

### 2. Nói về cốt truyện chung

```
"Cốt truyện phim xoay quanh mối quan hệ giữa cha và con.
Họ phải vượt qua nhiều khó khăn để hiểu nhau và cuối cùng đã hòa giải."
```

**Từ khóa phát hiện:** `cốt truyện`, `mối quan hệ`, `cha và con`, `khó khăn`, `hòa giải`
**Độ tin cậy:** ~70%

### 3. Nói về tình tiết hành động

```
"Phim có nhiều cảnh hành động gay cấn. Nhân vật chính phải chiến đấu với kẻ thù
và vượt qua nhiều thử thách để hoàn thành nhiệm vụ."
```

**Từ khóa phát hiện:** `cảnh hành động`, `nhân vật chính`, `kẻ thù`, `thử thách`, `nhiệm vụ`
**Độ tin cậy:** ~75%

### 4. Nói về phát triển nhân vật

```
"Character development của nhân vật chính rất tốt. Anh ta từ một người yếu đuối
trở thành một anh hùng dũng cảm sau khi trải qua nhiều thử thách."
```

**Từ khóa phát hiện:** `character development`, `nhân vật chính`, `anh hùng`, `thử thách`
**Độ tin cậy:** ~68%

### 5. Nói về quan hệ gia đình

```
"Phim tập trung vào mối quan hệ gia đình phức tạp. Cha mẹ và con cái
phải học cách hiểu nhau và vượt qua những khác biệt."
```

**Từ khóa phát hiện:** `quan hệ gia đình`, `cha mẹ`, `con cái`, `khác biệt`
**Độ tin cậy:** ~62%

---

## Độ Tin Cậy Thấp (40-60%) - Có dấu hiệu spoiler

### 1. Nói về diễn xuất

```
"Diễn xuất của nhân vật chính rất xuất sắc. Anh ta thể hiện được sự phức tạp
của nhân vật và làm cho khán giả đồng cảm với những gì nhân vật trải qua."
```

**Từ khóa phát hiện:** `diễn xuất`, `nhân vật chính`, `nhân vật trải qua`
**Độ tin cậy:** ~45%

### 2. Nói về đạo diễn

```
"Đạo diễn đã tạo ra một bộ phim có cốt truyện hấp dẫn. Cách kể chuyện
và phát triển nhân vật rất tinh tế và sâu sắc."
```

**Từ khóa phát hiện:** `đạo diễn`, `cốt truyện`, `phát triển nhân vật`
**Độ tin cậy:** ~50%

### 3. Nói về âm nhạc

```
"Âm nhạc trong phim rất phù hợp với không khí. Nhạc nền tạo ra cảm xúc
mạnh mẽ và làm tăng thêm sự căng thẳng của các cảnh quan trọng."
```

**Từ khóa phát hiện:** `âm nhạc`, `nhạc nền`, `cảnh quan trọng`
**Độ tin cậy:** ~42%

### 4. Nói về hiệu ứng

```
"Hiệu ứng đặc biệt trong phim rất ấn tượng. Các cảnh hành động
được thực hiện rất chân thực và tạo ra cảm giác hồi hộp."
```

**Từ khóa phát hiện:** `hiệu ứng đặc biệt`, `cảnh hành động`
**Độ tin cậy:** ~48%

### 5. Nói về bối cảnh

```
"Bối cảnh phim được thiết kế rất đẹp. Không gian và thời gian
được thể hiện rõ ràng và tạo ra không khí phù hợp cho câu chuyện."
```

**Từ khóa phát hiện:** `bối cảnh`, `không gian`, `thời gian`, `câu chuyện`
**Độ tin cậy:** ~40%

---

## Độ Tin Cậy Rất Thấp (< 40%) - Không có spoiler

### 1. Review kỹ thuật thuần túy

```
"Phim có diễn xuất xuất sắc và đạo diễn rất tài năng.
Âm nhạc và hiệu ứng đặc biệt tạo ra trải nghiệm xem phim tuyệt vời."
```

**Từ khóa phát hiện:** `diễn xuất`, `đạo diễn`, `âm nhạc`, `hiệu ứng đặc biệt`
**Độ tin cậy:** ~15%

### 2. Review cảm xúc

```
"Phim tạo ra cảm xúc mạnh mẽ cho người xem. Cách kể chuyện
và phát triển nhân vật làm cho khán giả đồng cảm sâu sắc."
```

**Từ khóa phát hiện:** `cảm xúc`, `kể chuyện`, `phát triển nhân vật`
**Độ tin cậy:** ~20%

### 3. Review phong cách

```
"Phong cách làm phim rất độc đáo. Đạo diễn sử dụng
nhiều kỹ thuật quay phim sáng tạo và tạo ra hình ảnh đẹp mắt."
```

**Từ khóa phát hiện:** `phong cách`, `đạo diễn`, `kỹ thuật quay phim`, `hình ảnh`
**Độ tin cậy:** ~10%

### 4. Review âm nhạc

```
"Âm nhạc trong phim rất hay. Nhạc nền phù hợp với từng cảnh
và tạo ra không khí phù hợp cho câu chuyện."
```

**Từ khóa phát hiện:** `âm nhạc`, `nhạc nền`, `cảnh`, `câu chuyện`
**Độ tin cậy:** ~12%

### 5. Review tổng quan

```
"Đây là một bộ phim hay với diễn xuất tốt, đạo diễn tài năng
và cốt truyện hấp dẫn. Đáng xem cho mọi lứa tuổi."
```

**Từ khóa phát hiện:** `diễn xuất`, `đạo diễn`, `cốt truyện`
**Độ tin cậy:** ~8%

---

## Các trường hợp đặc biệt

### 1. Có cảnh báo spoiler rõ ràng

```
"SPOILER ALERT: Phim có kết thúc bất ngờ khi nhân vật chính hóa ra là kẻ phản bội."
```

**Độ tin cậy:** ~95% (tự động đánh dấu spoiler)

### 2. Có từ khóa review giảm khả năng spoiler

```
"Review: Phim có cốt truyện hấp dẫn với nhiều tình tiết bất ngờ."
```

**Độ tin cậy:** ~35% (giảm do có từ "review")

### 3. Nội dung ngắn

```
"Phim hay."
```

**Độ tin cậy:** ~5% (quá ngắn để phân tích)

### 4. Nội dung dài với nhiều từ khóa

```
"Phim có cốt truyện phức tạp với nhiều nhân vật. Nhân vật chính phải đối mặt với nhiều thử thách.
Có những cảnh hành động gay cấn và tình tiết bất ngờ. Kết thúc phim thật sự làm tôi shock."
```

**Độ tin cậy:** ~85% (nhiều từ khóa + độ dài)

### 5. Có cả từ khóa spoiler và review

```
"Review: Phim có diễn xuất tốt nhưng kết thúc hơi bất ngờ."
```

**Độ tin cậy:** ~55% (cân bằng giữa spoiler và review)
