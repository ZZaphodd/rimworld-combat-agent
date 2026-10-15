"""찹쌀이's emotion from KOTE (tools/kote_mlx.py): every one of the model's 44 labels belongs to
exactly one of the avatar's five emotions. The model check runs only where MLX and the model
files are (.venv-chzzk after `tools/kote_mlx.py --fetch`)."""
import sys
import unittest

sys.path.insert(0, "tools")
import kote_mlx  # noqa: E402

KOTE_LABELS = (   # id2label of searle-j/kote_for_easygoing_people, in order
    "불평/불만", "환영/호의", "감동/감탄", "지긋지긋", "고마움", "슬픔", "화남/분노", "존경", "기대감",
    "우쭐댐/무시함", "안타까움/실망", "비장함", "의심/불신", "뿌듯함", "편안/쾌적", "신기함/관심",
    "아껴주는", "부끄러움", "공포/무서움", "절망", "한심함", "역겨움/징그러움", "짜증", "어이없음", "없음",
    "패배/자기혐오", "귀찮음", "힘듦/지침", "즐거움/신남", "깨달음", "죄책감", "증오/혐오",
    "흐뭇함(귀여움/예쁨)", "당황/난처", "경악", "부담/안_내킴", "서러움", "재미없음", "불쌍함/연민", "놀람",
    "행복", "불안/걱정", "기쁨", "안심/신뢰")


class GroupsTest(unittest.TestCase):
    def test_each_label_in_exactly_one_group(self):
        grouped = [label for labels in kote_mlx.GROUPS.values() for label in labels]
        self.assertEqual(len(grouped), len(set(grouped)))
        self.assertEqual(set(grouped), set(KOTE_LABELS))
        self.assertEqual(set(kote_mlx.GROUPS), {"calm", "joy", "surprise", "anger", "sad"})


@unittest.skipUnless(kote_mlx.mx is not None and (kote_mlx.DIR / "model.safetensors").exists(),
                     "needs MLX and the model files")
class ModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.k = kote_mlx.Kote()

    def test_labels_in_model_order(self):
        self.assertEqual(tuple(self.k.labels), KOTE_LABELS)

    def test_clear_lines(self):
        for text, emo in (("ㅋㅋㅋㅋ 개웃기네", "joy"), ("헐 대박 진짜?", "surprise"),
                          ("아 짜증나 왜 저기로 가", "anger"), ("오늘 너무 힘들다 ㅠㅠ", "sad"), ("안녕하세요", "calm")):
            self.assertEqual(self.k.emotion(text)[0], emo, text)

    def test_padding_does_not_change_a_line(self):
        one = self.k.scores(["헐 대박 진짜?"])[0]
        many = self.k.scores(["헐 대박 진짜?", "와 이걸 이기네 미쳤다 진짜 레전드 판이다"])[0]
        self.assertLess(max(abs(one[label] - many[label]) for label in one), 1e-4)


if __name__ == "__main__":
    unittest.main()
