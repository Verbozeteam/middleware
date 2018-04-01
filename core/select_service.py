from logs import Log

import sys
import select

#
# Base class for a "selectible" object, which can read/write using the SelectService
# Selectibles should override on_read_ready and implement it to read from the fd
# Selectibles should use write_to_fd to write to the fd (never use plain .write!)
#
class Selectible(object):
	def initialize_selectible_fd(self, fd):
		self.pending_write_to_fd = bytearray([])
		self.fd = fd
		self.write_function = "write" if "write" in dir(fd) else "send" # some have .write, some have .send
		SelectService.register_selectible(self)

	def destroy_selectible(self):
		SelectService.deregister_selectible(self)

	def write_to_fd(self, data):
		self.pending_write_to_fd += data

	def on_read_ready(self, cur_time_s):
		pass

	def on_write_ready(self, cur_time_s):
		try:
			# call the write function
			nsent = getattr(self.fd, self.write_function)(self.pending_write_to_fd)
			if nsent == None:
				print (self.fd, self.write_function, self, self.pending_write_to_fd)
				import traceback
				traceback.print_stack()
			if nsent <= 0:
				Log.debug("Selectible::on_write_ready() wrote 0 bytes")
				return False
			self.pending_write_to_fd = self.pending_write_to_fd[nsent:]
			return True
		except:
			Log.debug("Selectible::on_write_ready() failed.", exception=True)
			return False

#
# A simple select-based event pump
#
class SelectService(object):
	# a dictionary of selectible-string -> selectible
	selectibles = {}

	select_timeout = 0

	# Registers a selectible
	# selectible  A Selectible object
	@staticmethod
	def register_selectible(selectible):
		Log.info("registered selectible {}".format(str(selectible)))
		SelectService.selectibles[selectible.fd.fileno()] = selectible

	# Deregisters a selectible
	@staticmethod
	def deregister_selectible(selectible):
		Log.info("DEregistered selectible {}".format(str(selectible)))
		key = selectible.fd.fileno()
		if key in SelectService.selectibles:
			del SelectService.selectibles[key]

	# Performs a select with a timeout to wait for selectibles to be ready for reading or writing
	# cur_time_s  Current time in seconds
	@staticmethod
	def perform_select(cur_time_s, select_reads=True, select_writes=True):
		all_selectibles = SelectService.selectibles.values()

		read_descriptors = []
		write_descriptors = []

		if select_reads:
			readable_descriptors = dict(map(lambda s: (s.fd.fileno(), s), all_selectibles))
			read_descriptors = list(map(lambda rd: rd.fd, readable_descriptors.values()))

		if select_writes:
			writable_descriptors = dict(map(lambda s: (s.fd.fileno(), s), filter(lambda s: len(s.pending_write_to_fd) > 0, all_selectibles)))
			write_descriptors = list(map(lambda wd: wd.fd, writable_descriptors.values()))

		if len(read_descriptors) + len(write_descriptors) == 0:
			return # nothing to select

		try:
			(ready_read_descriptors, ready_write_descriptors, _) = select.select(read_descriptors, write_descriptors, [], SelectService.select_timeout)
			for D in ready_write_descriptors:
				fd = D.fileno()
				try:
					keep = writable_descriptors[fd].on_write_ready(cur_time_s)
				except:
					keep = False
				if not keep:
					writable_descriptors[fd].destroy_selectible()
			for D in ready_read_descriptors:
				fd = D.fileno()
				try:
					keep = readable_descriptors[fd].on_read_ready(cur_time_s)
				except:
					keep = False
				if not keep:
					readable_descriptors[fd].destroy_selectible()
		except KeyboardInterrupt:
			raise
		except:
			Log.debug("Select failed.", exception=True)

