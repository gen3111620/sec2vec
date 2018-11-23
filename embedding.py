from multiprocessing import cpu_count

import numpy as np
from glove import Glove, Corpus
from gensim.models import Word2Vec, FastText

from logger import EpochLogger
from preprocessing import KeywordCorpusFactory
from preprocessing import KeywordCorpusIterator


epoch_logger = EpochLogger()

class KeywordCorpusFactoryWord2VecMixin(Word2Vec, KeywordCorpusFactory): 

	def __init__(
		self, keywords, sentences, 
		corpus_worker, chunksize, case_sensitive, 
		corpus_file, size, alpha, 
		window, min_count, max_vocab_size, 
		sample, seed, workers, 
		min_alpha, sg, hs, 
		negative, ns_exponent, cbow_mean, 
		iter, null_word, trim_rule, 
		sorted_vocab, batch_words, compute_loss, 
		max_final_vocab):
		
		KeywordCorpusFactory.__init__(self, keywords, case_sensitive)
		self.kc = self.create(sentences, chunksize, corpus_worker)
		self.kv = dict(((keyword, []) for keyword in self.kc.keys()))
		self.corpus_worker = corpus_worker
		self.corpus_chunksize = corpus_chunksize
		
		Word2Vec.__init__(
			self, 
			corpus_file=corpus_file, size=size, 
			alpha=alpha, window=window, min_count=min_count,
			max_vocab_size=max_vocab_size, sample=sample, seed=seed, 
			workers=workers, min_alpha=min_alpha, sg=sg, 
			hs=hs, negative=negative, ns_exponent=ns_exponent, 
			cbow_mean=cbow_mean, iter=iter, null_word=null_word, 
			trim_rule=trim_rule, sorted_vocab=sorted_vocab, batch_words=batch_words, 
			compute_loss=compute_loss, max_final_vocab=max_final_vocab,
			callbacks=[epoch_logger])

	def __getitem__(self, word):
		return self.wv[word]
		

class KeywordCorpusFactoryFasttextMixin(FastText, KeywordCorpusFactory): 

	def __init__(
		self, keywords, sentences, 
		corpus_worker, corpus_chunksize, case_sensitive,
		window=5, min_count=5, max_vocab_size=None, 
		sample=0.001, seed=1, workers=cpu_count(), 
		min_alpha=0.0001, sg=0, hs=0, 
		negative=5, ns_exponent=0.75, cbow_mean=1, 
		iter=5, null_word=0, trim_rule=None, 
		sorted_vocab=1, batch_words=10000, compute_loss=False, 
		max_final_vocab=None):

		KeywordCorpusFactory.__init__(self, keywords, case_sensitive)
		self.kc = self.create(sentences, corpus_chunksize, corpus_worker)
		self.kv = dict(((keyword, []) for keyword in self.kc.keys()))
		self.corpus_worker = corpus_worker
		self.corpus_chunksize = corpus_chunksize

		FastText.__init__(self, 
			window, min_count, max_vocab_size, 
			sample, seed, workers, 
			min_alpha, sg, hs, 
			negative, ns_exponent, cbow_mean, 
			iter, null_word, trim_rule, 
			sorted_vocab, batch_words, compute_loss, 
			max_final_vocab)

	def __getitem__(self, word):
		return self.wv[word]


class SecWord2Vec(KeywordCorpusFactoryWord2VecMixin):

	def __init__(
		self, keywords, sentences, 
		corpus_worker=3, corpus_chunksize=256, case_sensitive=False, 
		corpus_file=None, size=100, alpha=0.025, 
		window=5, min_count=5, max_vocab_size=None, 
		sample=0.001, seed=1, workers=cpu_count(), 
		min_alpha=0.0001, sg=0, hs=0, 
		negative=5, ns_exponent=0.75, cbow_mean=1, 
		iter=5, null_word=0, trim_rule=None, 
		sorted_vocab=1, batch_words=10000, compute_loss=False, 
		max_final_vocab=None):
		
		super().__init__( 
			keywords, sentences, corpus_worker, 
			corpus_chunksize, case_sensitive, corpus_file, 
			size, alpha, window, 
			min_count, max_vocab_size, sample, 
			seed, workers, min_alpha, 
			sg, hs, negative, 
			ns_exponent, cbow_mean, iter, 
			null_word, trim_rule, sorted_vocab,
			batch_words, compute_loss, max_final_vocab)

		self.build_vocab(
			(token for tokens in KeywordCorpusIterator(self.kc) 
				for token in tokens))

	def _get_vec(self, token):

		if token in self.wv:
			return self.wv[token]
		else:
			return self.wv['unk']

	def _cal_kv(self):

		for keyword, tokens_list in self.kc.items():

			for tokens in tokens_list:

				kv = None

				for i, token in enumerate(tokens):

					if i: 
						kv += self._get_vec(token)
					else:
						kv = self._get_vec(token)

				kv /= (i+1)
				self.kv[keyword] = kv

	def train_embed(
		self, keywords=None, sentences=None, corpus_file=None, update=False,
		total_examples=None, total_words=None,  epochs=None, 
		start_alpha=None, end_alpha=None, word_count=0, 
		queue_factor=2, report_delay=1.0, compute_loss=False):

		epochs = epochs if epochs else self.epochs
		total_examples = total_examples if total_examples else self.corpus_count

		if update:

			self.build_vocab(sentences, update=update)

			# TODO: Update new keyword and its new corpus
			# if keywords:
			# 	for keyword in keywords:
			# 		if keyword not in 

			# update_keyword_corpus = self.create()

			self.train(
				sentences, corpus_file, 
				total_examples, total_words, epochs, 
				start_alpha, end_alpha, word_count, 
				queue_factor, report_delay, compute_loss)
		else:

			self.train(
				(token for tokens in KeywordCorpusIterator(self.kc)
					for token in tokens), 
				corpus_file, total_examples, total_words, epochs, 
				start_alpha, end_alpha, word_count, 
				queue_factor, report_delay, compute_loss)

		self._cal_kv()


class SecFastText(KeywordCorpusFactoryFasttextMixin):

	def __init__(
		self, sentences=None, corpus_file=None, 
		sg=0, hs=0, size=100, alpha=0.025, 
		window=5, min_count=5, max_vocab_size=None,
		word_ngrams=1, sample=0.001, seed=1, 
		workers=3, min_alpha=0.0001, negative=5, 
		ns_exponent=0.75, cbow_mean=1, iter=5, 
		null_word=0, min_n=3, max_n=6, sorted_vocab=1, 
		bucket=2000000, trim_rule=None, batch_words=10000):


		super().__init__(
			sentences=sentences, corpus_file=corpus_file, 
			sg=sg, hs=hs, size=size, alpha=alpha, 
			window=window, min_count=min_count, max_vocab_size=max_vocab_size,
			word_ngrams=word_ngrams, sample=sample, seed=seed, 
			workers=workers, min_alpha=min_alpha, negative=negative, 
			ns_exponent=ns_exponent, cbow_mean=cbow_mean, iter=iter, 
			null_word=null_word, min_n=min_n, max_n=max_n, sorted_vocab=sorted_vocab, 
			bucket=bucket, trim_rule=trim_rule, batch_words=batch_words)

		self.build_vocab(
			(token for tokens in KeywordCorpusIterator(self.kc) 
				for token in tokens))


	def train_embed(
		self, sentences=None, corpus_file=None, update=False,
		total_examples=None, total_words=None,  epochs=None, 
		start_alpha=None, end_alpha=None, word_count=0, 
		queue_factor=2, report_delay=1.0):

		epochs = epochs if epochs else self.epochs
		total_examples = total_examples if total_examples else self.corpus_count

		if update:

			self.build_vocab(sentences, update=update)
			self.train(
				sentences, corpus_file, 
				total_examples, total_words, epochs, 
				start_alpha, end_alpha, word_count, 
				queue_factor, report_delay, compute_loss)

		else:

			self.train(
				(token for tokens in KeywordCorpusIterator(self.kc)
					for token in tokens),
				corpus_file, 
				total_examples, total_words, epochs, 
				start_alpha, end_alpha, word_count, 
				queue_factor, report_delay, compute_loss
			)

class SecGloVe(Glove):

	pass

	# def train(
	# 	self, sentences=None, corpus_file=None, total_examples=None, 
	# 	total_words=None, epochs=None, start_alpha=None, end_alpha=None, 
	# 	word_count=0, queue_factor=2, report_delay=1.0, compute_loss=False):

	# 	self.train(
	# 		sentences=sentences, corpus_file=corpus_file, 
	# 		total_examples=total_examples, total_words=total_words, 
	# 		epochs=epochs, start_alpha=start_alpha, 
	# 		end_alpha=end_alpha, word_count=word_count, 
	# 		queue_factor=queue_factor, report_delay=report_delay, 
	# 		compute_loss=compute_loss)

