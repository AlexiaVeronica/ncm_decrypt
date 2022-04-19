from decrypt_takiyasha import new_decoder


class Main:
    def __init__(self, filename):
        self.filename = filename
        self.decoder_data = new_decoder(filename)

    def ncm_decode(self):
        return self.decoder_data, self.filename.replace(".ncm", ".flac")

    def mflac_decode(self):
        return self.decoder_data, self.filename.replace(".mflac", ".flac")

    def qmcflac_decode(self):
        return self.decoder_data, self.filename.replace(".qmcflac", ".flac")

    def kv2_decode(self):
        return self.decoder_data, self.filename.replace(".kv2", ".mp3")

    def save_decrypt_file(self, new_file_name: str, decrypt_data: list):
        with open(new_file_name, 'wb') as f:
            for block in decrypt_data:
                f.write(block)

    def run(self):
        if ".ncm" in self.filename:
            self.save_decrypt_file(*self.ncm_decode())

        if ".mflac" in self.filename:
            self.save_decrypt_file(*self.mflac_decode())

        if ".qmcflac" in self.filename:
            self.save_decrypt_file(*self.qmcflac_decode())

        if ".kv2" in self.filename:
            self.save_decrypt_file(*self.kv2_decode())


if __name__ == '__main__':
    Main('夏艺韩 - 游山恋.ncm').run()
